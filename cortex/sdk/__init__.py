"""
Cortex SDK - Python SDK for the Cortex Semantic Layer Platform.

Provides programmatic access to all Cortex features including metrics,
data sources, dashboards, and more.

Examples:
    Basic usage:
    >>> from cortex.sdk import CortexClient
    >>> client = CortexClient(mode="direct")
    >>> metrics = client.metrics.list()

    With context:
    >>> client = CortexClient(
    ...     mode="direct",
    ...     workspace_id=workspace_id,
    ...     environment_id=env_id
    ... )

    With hooks:
    >>> from cortex.sdk.hooks.builtin import LoggingHook, MetricsHook
    >>> client = CortexClient(
    ...     mode="direct",
    ...     hooks=[LoggingHook(), MetricsHook()]
    ... )

    API mode:
    >>> client = CortexClient(
    ...     mode="api",
    ...     host="http://localhost:9002/api/v1",
    ...     api_key="your-api-key"
    ... )
"""

# Core clients
from cortex.sdk.clients.client import CortexClient
from cortex.sdk.clients.async_client import AsyncCortexClient

# Configuration
from cortex.sdk.config.settings import CortexSDKSettings
from cortex.sdk.config.connection import ConnectionMode

# Exceptions
from cortex.sdk.exceptions.base import (
    CortexSDKError,
    CortexHTTPError,
    CortexNotFoundError,
    CortexValidationError,
    CortexAuthenticationError,
    CortexAuthorizationError,
    CortexServerError,
    CortexConnectionError,
    CortexTimeoutError,
    CortexConfigurationError,
)

# Auth providers
from cortex.sdk.auth.base import BaseAuthProvider, BaseStorageProvider
from cortex.sdk.auth.api_key import APIKeyAuthProvider
from cortex.sdk.auth.bearer import BearerTokenAuthProvider

# Hooks
from cortex.sdk.hooks.base import BaseHook, HookRegistry
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import (
    EventContext,
    MetricsEventContext,
    DataSourcesEventContext,
    FileStorageEventContext,
    DashboardsEventContext,
    QueryEventContext,
)
from cortex.sdk.hooks.builtin.logging import LoggingHook
from cortex.sdk.hooks.builtin.metrics import MetricsHook

# Events
from cortex.sdk.events.types import CortexEvents, HookEventType

# HTTP Clients (for advanced users)
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.clients.async_http_client import AsyncCortexHTTPClient

__version__ = "0.1.0"

__all__ = [
    # Main clients
    "CortexClient",
    "AsyncCortexClient",
    # Configuration
    "CortexSDKSettings",
    "ConnectionMode",
    # Exceptions
    "CortexSDKError",
    "CortexHTTPError",
    "CortexNotFoundError",
    "CortexValidationError",
    "CortexAuthenticationError",
    "CortexAuthorizationError",
    "CortexServerError",
    "CortexConnectionError",
    "CortexTimeoutError",
    "CortexConfigurationError",
    # Auth
    "BaseAuthProvider",
    "BaseStorageProvider",
    "APIKeyAuthProvider",
    "BearerTokenAuthProvider",
    # Hooks
    "BaseHook",
    "HookRegistry",
    "HookManager",
    "EventContext",
    "MetricsEventContext",
    "DataSourcesEventContext",
    "FileStorageEventContext",
    "DashboardsEventContext",
    "QueryEventContext",
    "LoggingHook",
    "MetricsHook",
    # Events
    "CortexEvents",
    "HookEventType",
    # HTTP Clients
    "CortexHTTPClient",
    "AsyncCortexHTTPClient",
]
