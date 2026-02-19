"""
Connection mode enum for Cortex SDK.

Defines the connection modes available for CortexClient.
"""
from enum import Enum


class ConnectionMode(str, Enum):
    """
    Connection mode for Cortex SDK client.

    Attributes:
        API: HTTP requests to FastAPI server (external users)
        DIRECT: Direct access to Core services (Analytics as Code, CLI)

    Examples:
        >>> mode = ConnectionMode.DIRECT
        >>> print(mode.value)
        'direct'

        >>> mode = ConnectionMode.API
        >>> print(mode.value)
        'api'
    """

    API = "api"
    DIRECT = "direct"
