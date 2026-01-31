"""GCS storage backend with smart local caching for SQLite"""
import os
from typing import Optional, Callable
from pathlib import Path
from cortex.core.connectors.api.sheets.storage.base import CortexFileStorageBackend
from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager


class CortexFileStorageGCSBackend(CortexFileStorageBackend):
    """GCS storage for CSV (cold) + Local cache for SQLite (hot)"""
    
    def __init__(self, bucket_name: str, prefix: str, cache_manager: CortexFileStorageCacheManager):
        from google.cloud import storage
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = prefix
        self.cache_manager = cache_manager
    
    def save_file(
        self,
        source_id: str,
        filename: str,
        data: bytes,
        overwrite: bool = False,
        path_generator: Optional[Callable[[str, str], str]] = None,
    ) -> str:
        """Save CSV file to GCS"""
        blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        
        if not overwrite and blob.exists():
            raise ValueError(f"File {filename} already exists in GCS")
        
        blob.upload_from_string(data)
        return f"gs://{self.bucket.name}/{blob_path}"
    
    def get_sqlite_path(
        self,
        source_id: str,
        path_generator: Optional[Callable[[str], str]] = None,
    ) -> str:
        """Get local path where SQLite DB will be created/accessed"""
        if path_generator:
            return path_generator(source_id)
        
        # Return a local path in the sqlite directory where the SQLite file will be created
        # The file will be uploaded to GCS later in save_sqlite()
        cache_path = Path(self.cache_manager.sqlite_dir) / f"{source_id}.db"
        return str(cache_path)
    
    def load_file(self, source_id: str, filename: str) -> Optional[bytes]:
        """Load a file from GCS storage"""
        blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        
        if not blob.exists():
            return None
        
        return blob.download_as_bytes()
    
    def list_files(self, source_id: str) -> list:
        """List all files for a data source in GCS"""
        prefix_path = f"{self.prefix}/inputs/{source_id}/"
        blobs = self.bucket.list_blobs(prefix=prefix_path)
        
        files = []
        for blob in blobs:
            # Extract filename from full path
            filename = blob.name.replace(prefix_path, "")
            if filename:  # Skip if empty (directory-like entry)
                files.append(filename)
        
        return files
    
    def save_sqlite(self, source_id: str, db_path: str) -> str:
        """Save SQLite database to GCS"""

        # Validate source file exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"SQLite database not found at {db_path} before GCS upload. "
                f"DuckDB may have failed to create the database file."
            )

        file_size = os.path.getsize(db_path)
        if file_size == 0:
            raise ValueError(
                f"SQLite database at {db_path} is empty (0 bytes) before GCS upload. "
                f"DuckDB conversion failed to write data."
            )

        blob_path = f"{self.prefix}/sqlite/{source_id}.db"
        blob = self.bucket.blob(blob_path)

        # Upload SQLite database file to GCS
        print(f"Uploading SQLite database to GCS: {blob_path} ({file_size} bytes)")
        blob.upload_from_filename(db_path)

        # Verify upload succeeded
        if not blob.exists():
            raise IOError(f"Failed to upload SQLite database to GCS at {blob_path}")

        # Return the GCS path as the canonical location
        # The local cache is for performance, GCS is the source of truth
        gcs_path = f"gs://{self.bucket.name}/{blob_path}"
        print(f"SQLite database uploaded successfully: {gcs_path}")
        return gcs_path
    
    def delete_file(self, source_id: str, filename: str) -> bool:
        """Delete a file from GCS storage"""
        blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        
        if not blob.exists():
            return False
        
        blob.delete()
        return True
    
    def exists(self, source_id: str, filename: str) -> bool:
        """Check if a file exists in GCS"""
        blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        return blob.exists()
    
    def download_file(self, remote_path: str, local_path: str):
        """Download file from GCS to local path"""
        blob = self.bucket.blob(remote_path)
        blob.download_to_filename(local_path)
