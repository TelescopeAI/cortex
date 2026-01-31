"""Background jobs module for Cortex data processing tasks"""
import json
import os

# Parse comma-separated ALLOWED_ORIGINS BEFORE importing anything else
# This must happen here because Plombery's Settings is instantiated at import time
# We need this before registry imports cache_eviction which imports plombery
from cortex.core.config.execution_env import ExecutionEnv

origins_str = ExecutionEnv.get_key("ALLOWED_ORIGINS", "*")
if origins_str != "*" and isinstance(origins_str, str):
    # Only parse if it's NOT already JSON (starts with '[')
    if not origins_str.startswith("["):
        # Convert "http://localhost:3000,http://localhost:3001" 
        # to JSON array: ["http://localhost:3000", "http://localhost:3001"]
        allowed_origins = [o.strip() for o in origins_str.split(",")]
        # Set as JSON string that Pydantic can validate
        os.environ["ALLOWED_ORIGINS"] = json.dumps(allowed_origins)

# NOW import the registry after env var is fixed
from cortex.jobs.registry import register_all_pipelines

__all__ = ["register_all_pipelines"]
