import os
import contextvars
from pathlib import Path
from typing import Optional
from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.connectors.api.sheets.types import CortexSheetsStorageType


class CortexSheetsConfig:
    """Configuration for Cortex Sheets data source"""
    
    # Storage type
    storage_type: CortexSheetsStorageType
    
    # Local storage paths
    input_storage_path: str  # Where uploaded files are stored
    sqlite_storage_path: str  # Where generated SQLite DBs are stored
    
    # Cache configuration
    cache_dir: str
    cache_max_size_gb: float
    cache_ttl_hours: int
    
    # GCS configuration (for cloud deployment)
    gcs_bucket: str
    gcs_prefix: str
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        # Storage type
        storage_type_str = ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_TYPE",
            CortexSheetsStorageType.LOCAL.value
        )
        self.storage_type = CortexSheetsStorageType(storage_type_str)
        
        # Get project root directory (six levels up from this file)
        # This file is at: cortex/cortex/core/connectors/api/sheets/config.py
        # Project root is: cortex/ (the repository root)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent.parent.parent
        
        # Input storage path (for uploaded files)
        self.input_storage_path = ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_INPUT_DIR",
            str(project_root / ".cortex" / "storage" / "inputs")
        )
        
        # SQLite storage path
        self.sqlite_storage_path = ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_SQLITE_DIR",
            str(project_root / ".cortex" / "storage" / "sqlite")
        )
        
        # Cache configuration
        self.cache_dir = ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_CACHE_DIR",
            str(project_root / ".cortex" / "cache" / "sqlite")
        )
        self.cache_max_size_gb = float(ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_CACHE_MAX_SIZE_GB",
            "10"  # 10GB default
        ))
        self.cache_ttl_hours = int(ExecutionEnv.get_key(
            "CORTEX_FILE_STORAGE_CACHE_TTL_HOURS",
            "168"  # 7 days default
        ))
        
        # GCS configuration
        self.gcs_bucket = ExecutionEnv.get_key("CORTEX_FILE_STORAGE_GCS_BUCKET", "")
        self.gcs_prefix = ExecutionEnv.get_key("CORTEX_FILE_STORAGE_GCS_PREFIX", "cortex-files")
        
        # Ensure directories exist for local storage
        if self.storage_type == CortexSheetsStorageType.LOCAL:
            self._ensure_local_directories()
    
    def _ensure_local_directories(self):
        """Create local storage directories if they don't exist"""
        Path(self.input_storage_path).mkdir(parents=True, exist_ok=True)
        Path(self.sqlite_storage_path).mkdir(parents=True, exist_ok=True)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> "CortexSheetsConfig":
        """Create config instance from environment variables"""
        return cls()


# Context variable for thread-safe, async-safe configuration storage
_sheets_config: contextvars.ContextVar[Optional[CortexSheetsConfig]] = (
    contextvars.ContextVar('sheets_config', default=None)
)


def get_sheets_config() -> CortexSheetsConfig:
    """Get or create the sheets config instance from context"""
    config = _sheets_config.get()
    if config is None:
        config = CortexSheetsConfig.from_env()
        _sheets_config.set(config)
    return config


def ensure_storage_directories():
    """Ensure storage directories exist"""
    config = get_sheets_config()
    Path(config.input_storage_path).mkdir(parents=True, exist_ok=True)
    Path(config.sqlite_storage_path).mkdir(parents=True, exist_ok=True)
    Path(config.cache_dir).mkdir(parents=True, exist_ok=True)
