"""Top-level entry point for Cortex: python -m cortex

Environment Variables:
    CORTEX_ENABLE_JOBS: Enable jobs server (true/false)
    CORTEX_FILE_STORAGE_TYPE: Storage type ('local', 'gcs', 's3')
                               - Jobs auto-enabled for 'gcs'
    CORTEX_API_HOST: API server host (default: 0.0.0.0)
    CORTEX_API_PORT: API server port (default: 9002)
    CORTEX_JOBS_HOST: Jobs server host (default: 0.0.0.0)
    CORTEX_JOBS_PORT: Jobs server port (default: 9003)

Usage:
    # Default: Start API only (jobs opt-in)
    python -m cortex
    
    # Enable jobs explicitly
    CORTEX_ENABLE_JOBS=true python -m cortex
    
    # Jobs auto-enabled when using GCS
    CORTEX_FILE_STORAGE_TYPE=gcs python -m cortex
"""
import json
import os

# Parse comma-separated ALLOWED_ORIGINS BEFORE importing jobs-related modules
# because Plombery's Settings is instantiated at import time
from cortex.core.config.execution_env import ExecutionEnv

origins_str = ExecutionEnv.get_key("ALLOWED_ORIGINS", "*")
if origins_str != "*" and isinstance(origins_str, str):
    # Convert "http://localhost:3000,http://localhost:3001" 
    # to JSON array: ["http://localhost:3000", "http://localhost:3001"]
    allowed_origins = [o.strip() for o in origins_str.split(",")]
    # Set as JSON string that Pydantic can validate
    os.environ["ALLOWED_ORIGINS"] = json.dumps(allowed_origins)

from cortex.app import create_data_app

if __name__ == "__main__":
    app = create_data_app(
        api_host=ExecutionEnv.get_key("CORTEX_API_HOST", "0.0.0.0"),
        api_port=int(ExecutionEnv.get_key("CORTEX_API_PORT", "9002")),
        jobs_host=ExecutionEnv.get_key("CORTEX_JOBS_HOST", "0.0.0.0"),
        jobs_port=int(ExecutionEnv.get_key("CORTEX_JOBS_PORT", "9003"))
    )
    app.start()
