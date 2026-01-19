"""Direct entry point for Jobs server: python -m cortex.jobs

Environment Variables:
    CORTEX_JOBS_HOST: Jobs server host (default: 0.0.0.0)
    CORTEX_JOBS_PORT: Jobs server port (default: 9003)

Usage:
    # Start jobs server only
    python -m cortex.jobs
    
    # With custom port
    CORTEX_JOBS_PORT=8080 python -m cortex.jobs
"""
import json
import os

# Parse comma-separated ALLOWED_ORIGINS BEFORE importing anything from cortex.jobs
# because Plombery's Settings is instantiated at import time
from cortex.core.config.execution_env import ExecutionEnv

origins_str = ExecutionEnv.get_key("ALLOWED_ORIGINS", "*")
if origins_str != "*" and isinstance(origins_str, str):
    # Convert "http://localhost:3000,http://localhost:3001" 
    # to JSON array: ["http://localhost:3000", "http://localhost:3001"]
    allowed_origins = [o.strip() for o in origins_str.split(",")]
    # Set as JSON string that Pydantic can validate
    os.environ["ALLOWED_ORIGINS"] = json.dumps(allowed_origins)

# NOW import the jobs server (after env var is fixed)
from cortex.jobs.server import start_jobs_server

if __name__ == "__main__":
    start_jobs_server(
        host=ExecutionEnv.get_key("CORTEX_JOBS_HOST", "0.0.0.0"),
        port=int(ExecutionEnv.get_key("CORTEX_JOBS_PORT", "9003")),
        reload=False
    )

