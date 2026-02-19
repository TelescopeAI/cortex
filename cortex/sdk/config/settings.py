"""
SDK configuration settings.

Loads configuration from environment variables with constructor overrides.
"""
import os
from typing import Optional

from cortex.core.types.telescope import TSModel
from cortex.sdk.config.connection import ConnectionMode


class CortexSDKSettings(TSModel):
    """
    Configuration settings for Cortex SDK.

    Loads from environment variables with constructor overrides.
    Uses TSModel for consistency with Cortex patterns.

    Attributes:
        mode: Connection mode (api or direct)
        host: API server host (for API mode, e.g., "http://localhost:9002/api/v1")
        api_key: API key for authentication (for API mode)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_backoff_factor: Exponential backoff factor for retries
        default_workspace_id: Default workspace ID
        default_environment_id: Default environment ID
        version: SDK version

    Examples:
        Load from environment:
        >>> settings = CortexSDKSettings()

        Override specific values:
        >>> settings = CortexSDKSettings(
        ...     mode=ConnectionMode.API,
        ...     host="https://api.cortex.example.com/api/v1",
        ...     api_key="my-api-key"
        ... )
    """

    # Connection settings
    mode: ConnectionMode = ConnectionMode.DIRECT
    host: Optional[str] = None
    api_key: Optional[str] = None

    # Timeout and retry settings
    timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0

    # Default context
    default_workspace_id: Optional[str] = None
    default_environment_id: Optional[str] = None

    # SDK metadata
    version: str = "0.1.0"

    def __init__(self, **data):
        """
        Initialize settings.

        Loads defaults from environment variables, then applies constructor overrides.
        """
        # Load from environment if not provided
        if "host" not in data:
            data["host"] = os.getenv("CORTEX_API_URL", os.getenv("CORTEX_API_HOST"))

        if "api_key" not in data:
            data["api_key"] = os.getenv("CORTEX_API_KEY")

        if "default_workspace_id" not in data:
            data["default_workspace_id"] = os.getenv("CORTEX_WORKSPACE_ID")

        if "default_environment_id" not in data:
            data["default_environment_id"] = os.getenv("CORTEX_ENVIRONMENT_ID")

        if "timeout" not in data:
            timeout_env = os.getenv("CORTEX_TIMEOUT")
            if timeout_env:
                try:
                    data["timeout"] = float(timeout_env)
                except ValueError:
                    pass

        if "max_retries" not in data:
            retries_env = os.getenv("CORTEX_MAX_RETRIES")
            if retries_env:
                try:
                    data["max_retries"] = int(retries_env)
                except ValueError:
                    pass

        super().__init__(**data)

    model_config = {
        "arbitrary_types_allowed": True
    }
