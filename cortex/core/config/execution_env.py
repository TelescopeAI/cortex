import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

from cortex.core.types.telescope import TSModel


class EnvLevel(Enum):
    LOCAL = "LOCAL"
    DEV = "DEV"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


# Load environment variables from .env files at module import time
def _load_env_files():
    """
    Load environment variables from .env files.
    
    Priority order:
    1. If CORTEX_ENV_FILE_PATH env variable is set, load from that path
    2. Otherwise, look for local.env in the current directory and parent directories
    3. Falls back to default dotenv behavior (searches for .env)
    
    This function is called on module import to ensure env vars are loaded
    before any code tries to access them.
    """
    # Check if user provided a custom env file path
    custom_env_path = os.getenv("CORTEX_ENV_FILE_PATH")
    
    if custom_env_path:
        # Load from custom path if provided
        env_path = Path(custom_env_path)
        if env_path.exists():
            print(f"Loading environment from custom path: {env_path}")
            load_dotenv(dotenv_path=env_path, override=False)
        else:
            # Log warning but don't fail - allow fallback to system env vars
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"CORTEX_ENV_FILE_PATH specified but file not found: {custom_env_path}")
    else:
        # Default behavior: load from local.env or .env (searches up directory tree)
        # override=False means existing environment variables take precedence
        if Path("local.env").exists():
            print("Loading environment from local.env")
            load_dotenv(dotenv_path="local.env", override=False)
        elif Path(".env").exists():
            print("Loading environment from .env")
            load_dotenv(override=False)
    
    # Debug: Print loaded variables (excluding sensitive ones)
    # Collect all keys that start with CORTEX_ or are exactly EXECUTION_ENV
    debug_keys = [key for key in os.environ if key.startswith("CORTEX_") or key == "EXECUTION_ENV"]
    
    # Sort for consistent output
    debug_keys.sort()
    
    print("-" * 30)
    print("Cortex Configuration:")
    for key in debug_keys:
        value = os.getenv(key)
        # Mask sensitive values
        if any(secret in key.upper() for secret in ["PASSWORD", "SECRET", "TOKEN", "KEY"]):
            print(f"  {key}: ********")
        else:
            print(f"  {key}: {value}")
    
    # Check for missing important variables (not in os.environ)
    if "EXECUTION_ENV" not in os.environ:
        print("  EXECUTION_ENV: [NOT SET]")
        
    print("-" * 30)


# Call this on module import to load env files early
_load_env_files()


class ExecutionEnv(TSModel):
    https: bool = False
    level: EnvLevel = EnvLevel.LOCAL
    profiling: bool = False

    @staticmethod
    def get_key(key: str, default: str | bool | None = None) -> str | bool | None:
        return os.getenv(key, default)

    @staticmethod
    def get_env():
        https_enabled = ExecutionEnv.https_enabled()
        level_env = ExecutionEnv.get_key('EXECUTION_ENV').upper()
        level = EnvLevel(level_env)
        return ExecutionEnv(https=https_enabled, level=level)

    @staticmethod
    def get_profile():
        https_enabled = ExecutionEnv.https_enabled()
        level_env = ExecutionEnv.get_key('EXECUTION_ENV').upper()
        level = EnvLevel(level_env)
        profiling_enabled = True if ExecutionEnv.get_key('ENABLE_PROFILING') == "True" else False
        return ExecutionEnv(https=https_enabled, level=level, profiling=profiling_enabled)

    @staticmethod
    def https_enabled() -> bool:
        https_enabled: bool = False
        https_enabled_value: str = ExecutionEnv.get_key('HTTPS')
        if https_enabled_value == "True" or https_enabled_value == "true":
            https_enabled = True
        return https_enabled

    @staticmethod
    def is_local() -> bool:
        return ExecutionEnv.get_env().level == EnvLevel.LOCAL

    @staticmethod
    def is_profiling_enabled() -> bool:
        if ExecutionEnv.get_profile().profiling:
            return True
