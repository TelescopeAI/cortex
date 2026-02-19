"""
Main Cortex SDK client.

Provides unified interface to all Cortex operations through resource managers.
"""
from typing import Any, List, Optional, Union
from uuid import UUID
import logging

from cortex.sdk.config import CortexSDKSettings, ConnectionMode
from cortex.sdk.transport import HTTPTransport, DirectTransport
from cortex.sdk.auth.base import BaseAuthProvider, BaseStorageProvider
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.managers import MetricsManager, FileStorageManager

logger = logging.getLogger(__name__)


class CortexClient:
    """
    Main Cortex SDK client for all operations.

    Provides unified access to all Cortex resources through resource managers.
    Supports two connection modes:
    - **API mode**: HTTP client to remote Cortex API server
    - **Direct mode**: Direct access to Core services (bypasses API)

    The client manages:
    - Workspace/environment context (set once, use everywhere)
    - Authentication and authorization
    - Hook system for logging, metrics, and custom behavior
    - Transport abstraction (HTTP or Direct)
    - Resource managers for all operations

    Attributes:
        workspace_id: Current workspace ID context
        environment_id: Current environment ID context
        hooks: Hook manager for dynamic hook management
        metrics: Metrics manager
        file_storage: File storage manager

    Examples:
        Basic usage (Direct mode):
        >>> client = CortexClient(mode="direct")
        >>> metrics = client.metrics.list()

        With context:
        >>> client = CortexClient(
        ...     mode="direct",
        ...     workspace_id=workspace_id,
        ...     environment_id=env_id
        ... )
        >>> metrics = client.metrics.list()  # Uses env_id from client

        API mode:
        >>> client = CortexClient(
        ...     mode="api",
        ...     host="http://localhost:9002/api/v1",
        ...     api_key="your-api-key"
        ... )

        With hooks:
        >>> from cortex.sdk.hooks.builtin import LoggingHook, MetricsHook
        >>> client = CortexClient(
        ...     mode="direct",
        ...     hooks=[LoggingHook(), MetricsHook()]
        ... )
    """

    def __init__(
        self,
        mode: Union[str, ConnectionMode] = ConnectionMode.DIRECT,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        environment_id: Optional[UUID] = None,
        timeout: int = 30,
        max_retries: int = 3,
        storage: Optional[Any] = None,
        auth_provider: Optional[BaseAuthProvider] = None,
        storage_provider: Optional[BaseStorageProvider] = None,
        hooks: Optional[List[BaseHook]] = None,
        settings: Optional[CortexSDKSettings] = None,
    ):
        """
        Initialize Cortex SDK client.

        Args:
            mode: Connection mode ("api" or "direct", defaults to "direct")
            host: API host URL (for API mode, e.g., "http://localhost:9002/api/v1")
            api_key: API key (for API mode)
            workspace_id: Default workspace ID
            environment_id: Default environment ID
            timeout: Request timeout in seconds (for API mode)
            max_retries: Max retry attempts (for API mode)
            storage: Direct storage instance (for Direct mode)
            auth_provider: Custom authentication provider
            storage_provider: Custom storage provider (multi-tenancy)
            hooks: List of hooks to register
            settings: Pre-configured settings object

        Examples:
            >>> client = CortexClient()  # Direct mode, default settings
            >>> client = CortexClient(mode="direct", environment_id=env_id)
            >>> client = CortexClient(
            ...     mode="api",
            ...     host="http://localhost:9002/api/v1",
            ...     api_key="my-key"
            ... )
        """
        # Convert string mode to enum
        if isinstance(mode, str):
            mode = ConnectionMode(mode.upper())

        # Use settings or create from params
        self._settings = settings or CortexSDKSettings(
            mode=mode,
            host=host,
            api_key=api_key,
            workspace_id=workspace_id,
            environment_id=environment_id,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Store context
        self._workspace_id = workspace_id
        self._environment_id = environment_id

        # Setup hooks
        self._hooks = HookManager()
        if hooks:
            for i, hook in enumerate(hooks):
                # Assign priority based on order (earlier hooks run first)
                priority = (i + 1) * 10
                self._hooks.add_hook(hook, priority=priority)

        # Create transport based on mode
        if self._settings.mode == ConnectionMode.API:
            logger.info(f"Initializing HTTP transport: {self._settings.host}")
            self._transport = HTTPTransport(
                host=self._settings.host,
                auth_provider=auth_provider,
                timeout=self._settings.timeout,
                max_retries=self._settings.max_retries,
                hooks=self._hooks,
            )
        else:
            logger.info("Initializing Direct transport")
            self._transport = DirectTransport(
                storage=storage,
                storage_provider=storage_provider,
                hooks=self._hooks,
            )

        # Initialize managers
        logger.debug("Initializing resource managers")
        self._init_managers()

    def _init_managers(self):
        """Initialize all resource managers."""
        # File storage (no dependencies)
        self.file_storage = FileStorageManager(
            transport=self._transport, client=self, hooks=self._hooks
        )

        # Metrics
        self.metrics = MetricsManager(
            transport=self._transport, client=self, hooks=self._hooks
        )

        # TODO: Add more managers as they're implemented
        # self.data_sources = DataSourcesManager(...)
        # self.metric_variants = MetricVariantsManager(...)
        # self.data_models = DataModelsManager(...)
        # self.dashboards = DashboardsManager(...)
        # self.workspaces = WorkspacesManager(...)
        # self.environments = EnvironmentsManager(...)

    @property
    def workspace_id(self) -> Optional[UUID]:
        """
        Get current workspace ID.

        Returns:
            Workspace ID or None
        """
        return self._workspace_id

    @property
    def environment_id(self) -> Optional[UUID]:
        """
        Get current environment ID.

        Returns:
            Environment ID or None
        """
        return self._environment_id

    def set_workspace(self, workspace_id: UUID) -> None:
        """
        Change workspace context.

        All subsequent operations will use this workspace ID unless overridden.

        Args:
            workspace_id: New workspace ID

        Examples:
            >>> client.set_workspace(workspace_id)
            >>> workspaces = client.workspaces.list()  # Uses workspace_id
        """
        self._workspace_id = workspace_id
        logger.debug(f"Workspace context set to: {workspace_id}")

    def set_environment(self, environment_id: UUID) -> None:
        """
        Change environment context.

        All subsequent operations will use this environment ID unless overridden.

        Args:
            environment_id: New environment ID

        Examples:
            >>> client.set_environment(environment_id)
            >>> metrics = client.metrics.list()  # Uses environment_id
        """
        self._environment_id = environment_id
        logger.debug(f"Environment context set to: {environment_id}")

    def with_workspace(self, workspace_id: UUID):
        """
        Context manager for temporary workspace switch.

        Args:
            workspace_id: Temporary workspace ID

        Returns:
            Context manager

        Examples:
            >>> with client.with_workspace(other_workspace_id):
            ...     # Operations use other_workspace_id
            ...     workspaces = client.workspaces.list()
            # Back to original workspace_id
        """
        return _WorkspaceContext(self, workspace_id)

    def with_environment(self, environment_id: UUID):
        """
        Context manager for temporary environment switch.

        Args:
            environment_id: Temporary environment ID

        Returns:
            Context manager

        Examples:
            >>> with client.with_environment(prod_env_id):
            ...     # Operations use prod_env_id
            ...     metrics = client.metrics.list()
            # Back to original environment_id
        """
        return _EnvironmentContext(self, environment_id)

    def with_storage(self, **credentials):
        """
        Context manager for temporary storage switch (multi-tenancy).

        Args:
            **credentials: Storage credentials (passed to storage_provider)

        Returns:
            Context manager

        Examples:
            >>> with client.with_storage(api_key="org2-key"):
            ...     metrics = client.metrics.list()  # Uses org2 storage
        """
        return _StorageContext(self, credentials)

    def close(self):
        """
        Close client and clean up resources.

        Closes transport connections and releases resources.

        Examples:
            >>> client.close()

            With context manager:
            >>> with CortexClient() as client:
            ...     metrics = client.metrics.list()
            # Auto-cleanup
        """
        logger.debug("Closing Cortex client")
        if self._transport:
            self._transport.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - auto cleanup."""
        self.close()


class _WorkspaceContext:
    """Context manager for temporary workspace switch."""

    def __init__(self, client: CortexClient, workspace_id: UUID):
        self._client = client
        self._new_workspace_id = workspace_id
        self._old_workspace_id = None

    def __enter__(self):
        self._old_workspace_id = self._client.workspace_id
        self._client.set_workspace(self._new_workspace_id)
        return self

    def __exit__(self, *args):
        if self._old_workspace_id is not None:
            self._client.set_workspace(self._old_workspace_id)


class _EnvironmentContext:
    """Context manager for temporary environment switch."""

    def __init__(self, client: CortexClient, environment_id: UUID):
        self._client = client
        self._new_environment_id = environment_id
        self._old_environment_id = None

    def __enter__(self):
        self._old_environment_id = self._client.environment_id
        self._client.set_environment(self._new_environment_id)
        return self

    def __exit__(self, *args):
        if self._old_environment_id is not None:
            self._client.set_environment(self._old_environment_id)


class _StorageContext:
    """Context manager for temporary storage switch."""

    def __init__(self, client: CortexClient, credentials: dict):
        self._client = client
        self._credentials = credentials
        # TODO: Implement storage switching when storage_provider is available

    def __enter__(self):
        logger.warning("Storage switching not yet implemented")
        return self

    def __exit__(self, *args):
        pass
