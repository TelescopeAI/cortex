"""Exceptions for file storage operations"""


class StorageFileAlreadyExists(Exception):
    """Raised when attempting to upload a file that already exists"""
    
    def __init__(self, filename: str, file_id: str):
        self.filename = filename
        self.file_id = file_id
        super().__init__(f"File '{filename}' already exists with ID {file_id}")
