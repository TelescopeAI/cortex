"""LRU cache manager for SQLite databases with GCS backing"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import pytz

from cortex.core.connectors.api.sheets.storage.base import CortexFileStorageBackend
from cortex.core.utils.data_sources import cleanup_empty_directories


class CortexFileStorageCacheManager:
    """Manages local SSD cache for SQLite databases with LRU eviction"""
    
    def __init__(self, cache_dir: str, sqlite_dir: str, max_size_gb: float):
        self.cache_dir = Path(cache_dir)        # For metadata only
        self.sqlite_dir = Path(sqlite_dir)      # For SQLite files
        self.max_size_gb = max_size_gb
        self.metadata_db = self.cache_dir / "file_storage_meta.db"  # Renamed for clarity
        self._init_metadata_db()
    
    def _init_metadata_db(self):
        """Initialize SQLite metadata database for cache tracking"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.metadata_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files_cache_entries (
                file_id TEXT PRIMARY KEY,
                local_path TEXT NOT NULL,
                remote_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                last_accessed TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def get_cached_path(
        self, 
        file_id: str, 
        remote_path: str,
        storage_backend: CortexFileStorageBackend
    ) -> str:
        """Get local path for SQLite DB, downloading from remote if needed"""
        # Check if file exists in cache
        local_path = self._get_cache_entry(file_id)
        
        if local_path and Path(local_path).exists():
            # Cache hit - update last accessed time
            self._update_last_accessed(file_id)
            return local_path
        
        # Cache miss - download from remote storage
        local_path = self._download_and_cache(
            file_id, 
            remote_path, 
            storage_backend
        )
        
        # Check if we need to evict
        self._check_and_evict_if_needed()
        
        return local_path
    
    def evict_lru(self) -> int:
        """Evict least recently used items if cache exceeds max size"""
        current_size_gb = self._get_cache_size_gb()
        
        if current_size_gb <= self.max_size_gb:
            return 0
        
        # Get entries sorted by last accessed (oldest first)
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_id, local_path, size_bytes 
            FROM files_cache_entries 
            ORDER BY last_accessed ASC
        """)
        
        evicted_count = 0
        bytes_to_free = (current_size_gb - self.max_size_gb) * 1024**3
        bytes_freed = 0
        
        base_paths = {self.cache_dir, self.sqlite_dir}

        for file_id, local_path, size_bytes in cursor.fetchall():
            if bytes_freed >= bytes_to_free:
                break

            # Delete file
            path_obj = Path(local_path)
            if path_obj.exists():
                path_obj.unlink()
                # Clean up empty parent directories
                cleanup_empty_directories(path_obj.parent, base_paths)

            # Remove from metadata
            conn.execute("DELETE FROM files_cache_entries WHERE file_id = ?", (file_id,))

            bytes_freed += size_bytes
            evicted_count += 1

        conn.commit()
        conn.close()

        return evicted_count
    
    def _get_cache_size_gb(self) -> float:
        """Calculate total cache size in GB by checking actual files on disk"""
        total_bytes = 0

        # Calculate size of all .db files in sqlite directory
        # No need to exclude metadata DB since it's in a different directory now
        for file_path in self.sqlite_dir.glob("*.db"):
            try:
                total_bytes += file_path.stat().st_size
            except (OSError, FileNotFoundError):
                pass
        
        # Also sync metadata with actual files - remove entries for files that no longer exist
        self._sync_metadata_with_disk()
        
        return total_bytes / (1024**3)
    
    def _get_cache_entry(self, file_id: str) -> Optional[str]:
        """Get cached file path if it exists"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT local_path FROM files_cache_entries WHERE file_id = ?",
            (file_id,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _update_last_accessed(self, file_id: str):
        """Update last accessed timestamp for a cache entry"""
        now = datetime.now(pytz.UTC)
        conn = sqlite3.connect(self.metadata_db)
        conn.execute(
            "UPDATE files_cache_entries SET last_accessed = ? WHERE file_id = ?",
            (now.isoformat(), file_id)
        )
        conn.commit()
        conn.close()
    
    def _sync_metadata_with_disk(self):
        """Remove metadata entries for files that no longer exist on disk"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT file_id, local_path FROM files_cache_entries")
        entries = cursor.fetchall()
        
        for file_id, local_path in entries:
            if not Path(local_path).exists():
                conn.execute("DELETE FROM files_cache_entries WHERE file_id = ?", (file_id,))
        
        conn.commit()
        conn.close()
    
    def _download_and_cache(
        self,
        file_id: str,
        remote_path: str,
        storage_backend: "CortexFileStorageBackend"
    ) -> str:
        """Download file from remote storage and cache it locally"""
        # Extract hierarchical path from remote path
        # remote_path formats:
        #   - gs://bucket/prefix/sqlite/workspace_id/environment_id/source_id.db
        #   - prefix/sqlite/workspace_id/environment_id/source_id.db
        # We want to preserve: workspace_id/environment_id/source_id.db

        # Try to extract the path after 'sqlite/' regardless of gs:// prefix
        try:
            if '/sqlite/' in remote_path:
                parts = remote_path.split('/sqlite/')
                if len(parts) > 1:
                    rel_path = parts[1]  # workspace_id/environment_id/source_id.db
                    local_path = str(self.sqlite_dir / rel_path)
                else:
                    # Fallback to flat structure
                    local_path = str(self.sqlite_dir / f"{file_id}.db")
            else:
                # No sqlite/ in path, use flat structure
                local_path = str(self.sqlite_dir / f"{file_id}.db")
        except Exception:
            # Fallback to flat structure on any error
            local_path = str(self.sqlite_dir / f"{file_id}.db")

        # Ensure parent directories exist
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        # Download file
        storage_backend.download_file(remote_path, local_path)
        
        # Get file size
        size_bytes = Path(local_path).stat().st_size
        
        # Record in metadata
        now = datetime.now(pytz.UTC)
        conn = sqlite3.connect(self.metadata_db)
        conn.execute(
            """INSERT INTO files_cache_entries 
               (file_id, local_path, remote_path, size_bytes, last_accessed, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file_id, local_path, remote_path, size_bytes, now.isoformat(), now.isoformat())
        )
        conn.commit()
        conn.close()
        
        return local_path
    
    def get_entries_count(self) -> int:
        """Get total number of cache entries"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM files_cache_entries")
        count = cursor.fetchone()[0] or 0
        conn.close()
        return count
    
    def _check_and_evict_if_needed(self):
        """Check if cache exceeds max size and evict if necessary"""
        current_size_gb = self._get_cache_size_gb()
        if current_size_gb > self.max_size_gb:
            self.evict_lru()

    def add_cache_entry(self, file_id: str, local_path: str, remote_path: str):
        """
        Add an existing local file to the cache metadata.

        This is used when uploading a file to GCS - we want to keep the local
        copy cached so immediate queries don't need to download from GCS.

        Args:
            file_id: Unique identifier for the file
            local_path: Path to the local file (already exists)
            remote_path: GCS path where file was uploaded
        """
        if not Path(local_path).exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        # Get file size
        size_bytes = Path(local_path).stat().st_size

        # Check if entry already exists
        existing = self._get_cache_entry(file_id)

        now = datetime.now(pytz.UTC)
        conn = sqlite3.connect(self.metadata_db)

        if existing:
            # Update existing entry
            conn.execute(
                """UPDATE files_cache_entries
                   SET local_path = ?, remote_path = ?, size_bytes = ?, last_accessed = ?
                   WHERE file_id = ?""",
                (local_path, remote_path, size_bytes, now.isoformat(), file_id)
            )
        else:
            # Insert new entry
            conn.execute(
                """INSERT INTO files_cache_entries
                   (file_id, local_path, remote_path, size_bytes, last_accessed, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (file_id, local_path, remote_path, size_bytes, now.isoformat(), now.isoformat())
            )

        conn.commit()
        conn.close()

        # Check if we need to evict after adding
        self._check_and_evict_if_needed()

    def delete_cache_entry(self, file_id: str) -> bool:
        """
        Delete a cache entry and its local file.

        Args:
            file_id: The file ID to remove from cache

        Returns:
            True if entry was found and deleted, False otherwise
        """
        # Get cache entry
        cache_entry = self._get_cache_entry(file_id)
        if not cache_entry:
            return False

        # Delete local cached file if exists
        local_path = Path(cache_entry)
        if local_path.exists():
            local_path.unlink()

            # Clean up empty parent directories
            # Stop at cache_dir (metadata) and sqlite_dir (base)
            base_paths = {self.cache_dir, self.sqlite_dir}
            cleanup_empty_directories(local_path.parent, base_paths)

        # Remove from metadata
        conn = sqlite3.connect(self.metadata_db)
        conn.execute("DELETE FROM files_cache_entries WHERE file_id = ?", (file_id,))
        conn.commit()
        conn.close()

        return True
