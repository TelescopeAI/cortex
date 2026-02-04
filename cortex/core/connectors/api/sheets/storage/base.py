from abc import ABC, abstractmethod
from typing import Optional, List, Callable


class CortexFileStorageBackend(ABC):
    """Abstract base class for file storage backends"""
    
    @abstractmethod
    def save_file(
        self,
        source_id: str,
        filename: str,
        data: bytes,
        overwrite: bool = False,
        path_generator: Optional[Callable] = None,
    ) -> str:
        """
        Save a file (CSV or raw data) to storage
        
        Args:
            source_id: Unique identifier for the data source
            filename: Name of the file to save
            data: File contents as bytes
            overwrite: Whether to overwrite existing file
            path_generator: Optional custom path generator function
            
        Returns:
            Path or URI where the file was saved
        """
        pass
    
    @abstractmethod
    def load_file(self, source_id: str, filename: str) -> Optional[bytes]:
        """
        Load a file from storage
        
        Args:
            source_id: Unique identifier for the data source
            filename: Name of the file to load
            
        Returns:
            File contents as bytes, or None if file doesn't exist
        """
        pass
    
    @abstractmethod
    def list_files(self, source_id: str) -> List[str]:
        """
        List all files for a data source
        
        Args:
            source_id: Unique identifier for the data source
            
        Returns:
            List of filenames
        """
        pass
    
    @abstractmethod
    def save_sqlite(self, source_id: str, db_path: str) -> str:
        """
        Save SQLite database file (or copy it to storage location)
        
        Args:
            source_id: Unique identifier for the data source
            db_path: Local path to the SQLite database file
            
        Returns:
            Path or URI where the database was saved
        """
        pass
    
    @abstractmethod
    def get_sqlite_path(
        self,
        source_id: str,
        path_generator: Optional[Callable] = None,
    ) -> str:
        """
        Get the path/URI to the SQLite database for a data source
        
        Args:
            source_id: Unique identifier for the data source
            path_generator: Optional custom path generator function
            
        Returns:
            Path or URI to the SQLite database
        """
        pass
    
    @abstractmethod
    def delete_file(self, source_id: str, filename: str) -> bool:
        """
        Delete a file from storage

        Args:
            source_id: Unique identifier for the data source
            filename: Name of the file to delete

        Returns:
            True if deleted, False if file didn't exist
        """
        pass

    @abstractmethod
    def delete_sqlite(self, sqlite_path: str) -> bool:
        """
        Delete a SQLite database file from storage

        Args:
            sqlite_path: Full path to SQLite file (local or GCS path)

        Returns:
            True if file was deleted, False if not found
        """
        pass

    @abstractmethod
    def exists(self, source_id: str, filename: str) -> bool:
        """
        Check if a file exists
        
        Args:
            source_id: Unique identifier for the data source
            filename: Name of the file to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    def download_file(self, remote_path: str, local_path: str) -> None:
        """
        Download a file from remote storage to local path
        
        Optional method for backends that support remote file access (e.g., GCS, S3).
        Not required for local file storage backends.
        
        Args:
            remote_path: Remote path or identifier for the file
            local_path: Local destination path
            
        Raises:
            NotImplementedError: If the backend doesn't support remote downloads
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support remote file downloads"
        )
