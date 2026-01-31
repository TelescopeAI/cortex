"""File path encryption utilities"""
from cryptography.fernet import Fernet
from cortex.core.config.execution_env import ExecutionEnv


class FilePathEncryption:
    """Encrypt and decrypt file paths using Fernet (AES) encryption"""
    
    @staticmethod
    def get_key() -> bytes:
        """Get encryption key from environment variable"""
        key = ExecutionEnv.get_key("CORTEX_FILE_STORAGE_ENCRYPTION_KEY")
        if not key:
            raise ValueError("CORTEX_FILE_STORAGE_ENCRYPTION_KEY environment variable is not set")
        return key.encode()
    
    @staticmethod
    def encrypt(path: str) -> str:
        """Encrypt a file path"""
        f = Fernet(FilePathEncryption.get_key())
        return f.encrypt(path.encode()).decode()
    
    @staticmethod
    def decrypt(encrypted_path: str) -> str:
        """Decrypt a file path"""
        f = Fernet(FilePathEncryption.get_key())
        return f.decrypt(encrypted_path.encode()).decode()
