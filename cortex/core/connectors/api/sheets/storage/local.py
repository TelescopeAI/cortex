import os
import shutil
from pathlib import Path
from typing import Optional, List, Callable
from cortex.core.connectors.api.sheets.storage.base import CortexFileStorageBackend
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.core.connectors.api.sheets.exceptions import StorageFileAlreadyExists


class CortexLocalFileStorage(CortexFileStorageBackend):
    """Local filesystem storage backend for spreadsheet data"""
    
    def __init__(self):
        """Initialize local storage backend"""
        self.config = get_sheets_config()
        self.base_input_path = Path(self.config.input_storage_path)
        self.base_sqlite_path = Path(self.config.sqlite_storage_path)
        
        # Ensure directories exist
        self.base_input_path.mkdir(parents=True, exist_ok=True)
        self.base_sqlite_path.mkdir(parents=True, exist_ok=True)
    
    def _get_source_dir(self, source_id: str) -> Path:
        """Get the directory path for a source's files"""
        return self.base_input_path / source_id
    
    def save_file(
        self,
        source_id: str,
        filename: str,
        data: bytes,
        overwrite: bool = False,
        path_generator: Optional[Callable[[str, str], str]] = None,
    ) -> str:
        """Save a file to local storage
        
        Args:
            source_id: Source/session ID for organizing files
            filename: Original filename with extension
            data: File content as bytes
            overwrite: Whether to overwrite existing file
            
        Returns:
            Full path to saved file
            
        Raises:
            StorageFileAlreadyExists: If file exists and overwrite=False
        """
        
        if path_generator:
            file_path = Path(path_generator(source_id, filename))
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            source_dir = self._get_source_dir(source_id)
            source_dir.mkdir(parents=True, exist_ok=True)
            file_path = source_dir / filename
        
        # Check if file exists
        if file_path.exists() and not overwrite:
            raise StorageFileAlreadyExists(filename, source_id)
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)
    
    def load_file(self, source_id: str, filename: str) -> Optional[bytes]:
        """Load a file from local storage"""
        source_dir = self._get_source_dir(source_id)
        file_path = source_dir / filename
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    def list_files(self, source_id: str) -> List[str]:
        """List all files for a data source"""
        source_dir = self._get_source_dir(source_id)
        
        if not source_dir.exists():
            return []
        
        return [f.name for f in source_dir.iterdir() if f.is_file()]
    
    def save_sqlite(self, source_id: str, db_path: str) -> str:
        """Save or copy SQLite database to storage location"""
        self.base_sqlite_path.mkdir(parents=True, exist_ok=True)
        
        dest_path = self.base_sqlite_path / f"{source_id}.db"
        
        # Copy the database file
        if os.path.exists(db_path):
            shutil.copy2(db_path, dest_path)
        
        return str(dest_path)
    
    def get_sqlite_path(
        self,
        source_id: str,
        path_generator: Optional[Callable[[str], str]] = None,
    ) -> str:
        """Get the path to the SQLite database for a data source"""
        if path_generator:
            return path_generator(source_id)
        return str(self.base_sqlite_path / f"{source_id}.db")
    
    def delete_file(self, source_id: str, filename: str) -> bool:
        """Delete a file from storage"""
        source_dir = self._get_source_dir(source_id)
        file_path = source_dir / filename
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def exists(self, source_id: str, filename: str) -> bool:
        """Check if a file exists"""
        source_dir = self._get_source_dir(source_id)
        file_path = source_dir / filename
        
        return file_path.exists()
