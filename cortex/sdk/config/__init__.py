"""
SDK configuration module.

Exports:
    - ConnectionMode: Enum for connection modes
    - CortexSDKSettings: Configuration settings class
"""
from cortex.sdk.config.connection import ConnectionMode
from cortex.sdk.config.settings import CortexSDKSettings

__all__ = ["ConnectionMode", "CortexSDKSettings"]
