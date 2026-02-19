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
        if path_generator:
            # Use custom path generator for hierarchical structure
            local_path = path_generator(source_id, filename)
            # Convert local path to GCS blob path
            # Path format: /path/to/.cortex/storage/inputs/workspace_id/environment_id/source_id/filename.csv
            # Extract everything after "inputs/"
            if "/inputs/" in local_path:
                relative_path = local_path.split("/inputs/", 1)[1]
                blob_path = f"{self.prefix}/inputs/{relative_path}"
            else:
                # Fallback if path doesn't contain "inputs/"
                blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        else:
            # Fallback to flat structure
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
    
    def load_file(
        self,
        source_id: Optional[str] = None,
        filename: Optional[str] = None,
        blob_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Load a file from GCS storage

        Args:
            source_id: Source ID for flat structure (legacy, optional)
            filename: Filename for flat structure (legacy, optional)
            blob_path: Full blob path within bucket (takes precedence if provided)
                      Supports hierarchical paths from database

        Returns:
            File contents as bytes, or None if not found
        """
        if blob_path:
            # Use provided blob path directly (supports hierarchical structure)
            blob = self.bucket.blob(blob_path)
        elif source_id and filename:
            # Construct path from source_id/filename (legacy flat structure)
            constructed_path = f"{self.prefix}/inputs/{source_id}/{filename}"
            blob = self.bucket.blob(constructed_path)
        else:
            raise ValueError("Either blob_path or both source_id and filename must be provided")

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

        # Extract hierarchical path from local db_path
        # db_path format: /path/to/sqlite/workspace_id/environment_id/source_id.db
        # We need to preserve the hierarchy in GCS
        from pathlib import Path
        sqlite_dir = Path(self.cache_manager.sqlite_dir)
        db_path_obj = Path(db_path)

        # Get relative path from sqlite_dir to preserve hierarchy
        try:
            rel_path = db_path_obj.relative_to(sqlite_dir)
        except ValueError:
            # Fallback: if path is not under sqlite_dir, use flat structure
            rel_path = Path(f"{source_id}.db")

        # Build GCS blob path with hierarchy
        blob_path = f"{self.prefix}/sqlite/{rel_path}"
        blob = self.bucket.blob(blob_path)

        # Upload SQLite database file to GCS
        print(f"Uploading SQLite database to GCS: {blob_path} ({file_size} bytes)")
        blob.upload_from_filename(db_path)

        # Verify upload succeeded
        if not blob.exists():
            raise IOError(f"Failed to upload SQLite database to GCS at {blob_path}")

        # Add local file to cache metadata so queries can use it immediately
        # without needing to download from GCS
        gcs_path = f"gs://{self.bucket.name}/{blob_path}"
        self.cache_manager.add_cache_entry(
            file_id=source_id,
            local_path=db_path,
            remote_path=gcs_path
        )

        # Return the GCS path as the canonical location
        # The local cache is for performance, GCS is the source of truth
        print(f"SQLite database uploaded successfully: {gcs_path}")
        print(f"Local file cached at: {db_path}")
        return gcs_path
    
    def delete_file(self, source_id: str, filename: str) -> bool:
        """Delete a file from GCS storage"""
        blob_path = f"{self.prefix}/inputs/{source_id}/{filename}"
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            return False

        blob.delete()
        return True

    def delete_sqlite(self, sqlite_path: str) -> bool:
        """Delete a SQLite database file from GCS storage"""
        # sqlite_path format: gs://bucket/prefix/sqlite/workspace_id/environment_id/source_id.db

        if not sqlite_path.startswith('gs://'):
            return False

        # Extract blob path from gs:// URI
        blob_path = sqlite_path.replace(f'gs://{self.bucket.name}/', '')
        blob = self.bucket.blob(blob_path)

        if not blob.exists():
            return False

        # Delete from GCS
        blob.delete()
        print(f"Deleted SQLite file from GCS: {sqlite_path}")

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
