"""
Async Cortex SDK client.

Provides async interface to all Cortex operations through handlers.
"""
from typing import Optional, List, Union
from uuid import UUID
import asyncio
import logging

from cortex.sdk.config import CortexSDKSettings, ConnectionMode
from cortex.sdk.clients.async_http_client import AsyncCortexHTTPClient
from cortex.sdk.auth.base import BaseAuthProvider
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.manager import HookManager

# Handler imports for explicit initialization
from cortex.sdk.handlers.metrics.base import MetricsHandler
from cortex.sdk.handlers.metric_variants.base import MetricVariantsHandler
from cortex.sdk.handlers.data_sources.base import DataSourcesHandler
from cortex.sdk.handlers.file_storage.base import FileStorageHandler
from cortex.sdk.handlers.data_models.base import DataModelsHandler
from cortex.sdk.handlers.dashboards.base import DashboardsHandler
from cortex.sdk.handlers.workspaces.base import WorkspacesHandler
from cortex.sdk.handlers.environments.base import EnvironmentsHandler
from cortex.sdk.handlers.consumers.base import ConsumersHandler
from cortex.sdk.handlers.consumer_groups.base import ConsumerGroupsHandler
from cortex.sdk.handlers.query_history.base import QueryHistoryHandler
from cortex.sdk.handlers.preaggregations.base import PreAggregationsHandler
from cortex.sdk.handlers.admin.base import AdminHandler

logger = logging.getLogger(__name__)


class AsyncCortexClient:
    """
    Async Cortex SDK client for all operations.

    Provides unified async access to all Cortex resources through handlers.
    Supports two connection modes:
    - **Direct mode**: Local Core service access (wrapped in async)
    - **API mode**: Async HTTP client to remote Cortex API server

    Attributes:
        workspace_id: Current workspace ID context
        environment_id: Current environment ID context
        hooks: Hook manager for dynamic hook management
        metrics: Metrics handler (async wrapper)
        (... other handlers as they're implemented)

    Examples:
        Direct mode (local):
        >>> async with AsyncCortexClient(mode="direct") as client:
        ...     metrics = await client.metrics.list(environment_id=env_id)

        API mode (remote server):
        >>> async with AsyncCortexClient(
        ...     mode="api",
        ...     host="http://localhost:9002/api/v1",
        ...     api_key="your-api-key"
        ... ) as client:
        ...     metrics = await client.metrics.list(environment_id=env_id)

        With context:
        >>> client = AsyncCortexClient(
        ...     mode="direct",
        ...     workspace_id=workspace_id,
        ...     environment_id=env_id
        ... )
        >>> metrics = await client.metrics.list()  # Uses env_id from client
        >>> await client.close()

        With hooks:
        >>> from cortex.sdk.hooks.builtin import LoggingHook
        >>> async with AsyncCortexClient(
        ...     mode="direct",
        ...     hooks=[LoggingHook()]
        ... ) as client:
        ...     metrics = await client.metrics.list(environment_id=env_id)

    Note:
        For Direct mode, synchronous Core operations are wrapped using asyncio.to_thread()
        to run in a thread pool. For API mode, native async HTTP operations are used.
    """

    # Handler attributes (type-hinted for IDE support)
    # Note: These will be _AsyncHandlerWrapper instances, but typed as base handlers
    metrics: MetricsHandler
    metric_variants: MetricVariantsHandler
    data_sources: DataSourcesHandler
    file_storage: FileStorageHandler
    data_models: DataModelsHandler
    dashboards: DashboardsHandler
    workspaces: WorkspacesHandler
    environments: EnvironmentsHandler
    consumers: ConsumersHandler
    consumer_groups: ConsumerGroupsHandler
    query_history: QueryHistoryHandler
    preaggregations: PreAggregationsHandler
    admin: AdminHandler

    def __init__(
        self,
        mode: Union[str, ConnectionMode] = ConnectionMode.DIRECT,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        environment_id: Optional[UUID] = None,
        timeout: int = 30,
        max_retries: int = 3,
        auth_provider: Optional[BaseAuthProvider] = None,
        hooks: Optional[List[BaseHook]] = None,
        settings: Optional[CortexSDKSettings] = None,
    ):
        """
        Initialize async Cortex SDK client.

        Args:
            mode: Connection mode ("api" or "direct", defaults to "direct")
            host: API host URL (required for API mode, e.g. "http://localhost:9002/api/v1")
            api_key: API key (for API mode authentication)
            workspace_id: Default workspace ID context
            environment_id: Default environment ID context
            timeout: Request timeout in seconds (for API mode)
            max_retries: Maximum retry attempts (for API mode)
            auth_provider: Custom authentication provider (for API mode)
            hooks: List of hooks to register
            settings: Pre-configured settings object

        Examples:
            >>> client = AsyncCortexClient()  # Direct mode
            >>> client = AsyncCortexClient(
            ...     mode="api",
            ...     host="http://localhost:9002/api/v1",
            ...     api_key="key"
            ... )
        """
        # Convert string mode to enum
        if isinstance(mode, str):
            mode = ConnectionMode(mode.lower())

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
                priority = (i + 1) * 10
                self._hooks.add_hook(hook, priority=priority)

        # Create async HTTP client if in API mode
        self._http_client = None
        if self._settings.mode == ConnectionMode.API:
            if not self._settings.host:
                raise ValueError("host is required for API mode")

            logger.info(f"Initializing async API mode: {self._settings.host}")
            self._http_client = AsyncCortexHTTPClient(
                host=self._settings.host,
                auth_provider=auth_provider,
                timeout=self._settings.timeout,
                max_retries=self._settings.max_retries,
            )
        else:
            logger.info("Initializing async Direct mode (thread pool)")

        # Initialize handlers
        self._init_handlers()

    def _init_handlers(self):
        """Initialize all handlers explicitly with async wrappers."""
        # Prepare context for handlers
        client_context = {
            "workspace_id": self._workspace_id,
            "environment_id": self._environment_id,
        }

        logger.debug("Initializing handlers for async client...")

        # Initialize and wrap each handler explicitly
        self.metrics = _AsyncHandlerWrapper(
            MetricsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.metric_variants = _AsyncHandlerWrapper(
            MetricVariantsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.data_sources = _AsyncHandlerWrapper(
            DataSourcesHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.file_storage = _AsyncHandlerWrapper(
            FileStorageHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.data_models = _AsyncHandlerWrapper(
            DataModelsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.dashboards = _AsyncHandlerWrapper(
            DashboardsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.workspaces = _AsyncHandlerWrapper(
            WorkspacesHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.environments = _AsyncHandlerWrapper(
            EnvironmentsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.consumers = _AsyncHandlerWrapper(
            ConsumersHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.consumer_groups = _AsyncHandlerWrapper(
            ConsumerGroupsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.query_history = _AsyncHandlerWrapper(
            QueryHistoryHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.preaggregations = _AsyncHandlerWrapper(
            PreAggregationsHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        self.admin = _AsyncHandlerWrapper(
            AdminHandler(
                mode=self._settings.mode,
                http_client=self._http_client,
                hooks=self._hooks,
                client_context=client_context,
            ),
            self._settings.mode,
        )

        logger.debug("All async handlers initialized")

    @property
    def workspace_id(self) -> Optional[UUID]:
        """
        Get current workspace ID context.

        Returns:
            Workspace ID or None
        """
        return self._workspace_id

    @property
    def environment_id(self) -> Optional[UUID]:
        """
        Get current environment ID context.

        Returns:
            Environment ID or None
        """
        return self._environment_id

    def set_workspace(self, workspace_id: UUID) -> None:
        """
        Change workspace context for all subsequent operations.

        Args:
            workspace_id: New workspace ID

        Examples:
            >>> client.set_workspace(workspace_id)
            >>> # All operations now use this workspace_id by default
        """
        self._workspace_id = workspace_id
        logger.debug(f"Workspace context set to: {workspace_id}")

    def set_environment(self, environment_id: UUID) -> None:
        """
        Change environment context for all subsequent operations.

        Args:
            environment_id: New environment ID

        Examples:
            >>> client.set_environment(environment_id)
            >>> metrics = await client.metrics.list()  # Uses this environment_id
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
            ...     pass
            # Back to original workspace_id
        """
        return _AsyncWorkspaceContext(self, workspace_id)

    def with_environment(self, environment_id: UUID):
        """
        Context manager for temporary environment switch.

        Args:
            environment_id: Temporary environment ID

        Returns:
            Context manager

        Examples:
            >>> with client.with_environment(prod_env_id):
            ...     metrics = await client.metrics.list()  # Uses prod_env_id
            # Back to original environment_id
        """
        return _AsyncEnvironmentContext(self, environment_id)

    async def close(self):
        """
        Close async client and clean up resources.

        Examples:
            >>> await client.close()

            With context manager:
            >>> async with AsyncCortexClient() as client:
            ...     metrics = await client.metrics.list(environment_id=env_id)
            # Auto-cleanup
        """
        logger.debug("Closing async Cortex client")
        if self._http_client:
            await self._http_client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit - auto cleanup."""
        await self.close()


class _AsyncHandlerWrapper:
    """
    Wrapper to make synchronous handlers async-compatible.

    For Direct mode: Wraps sync calls in asyncio.to_thread()
    For API mode: Uses async HTTP client (already async)
    """

    def __init__(self, handler, mode: ConnectionMode):
        """
        Initialize async handler wrapper.

        Args:
            handler: Synchronous handler instance
            mode: Connection mode
        """
        self._handler = handler
        self._mode = mode

    def __getattr__(self, name):
        """
        Wrap handler methods to make them async.

        Args:
            name: Method name

        Returns:
            Async wrapper function
        """
        attr = getattr(self._handler, name)

        # If it's not a callable method, return as-is
        if not callable(attr):
            return attr

        # Wrap method in async function
        async def async_wrapper(*args, **kwargs):
            # For Direct mode, run in thread pool
            # For API mode with async HTTP client, methods are already async-compatible
            if self._mode == ConnectionMode.DIRECT:
                # Run synchronous Core operations in thread pool
                return await asyncio.to_thread(attr, *args, **kwargs)
            else:
                # For API mode, handlers use async HTTP client methods
                # However, handlers themselves are sync, so wrap them too
                return await asyncio.to_thread(attr, *args, **kwargs)

        return async_wrapper


class _AsyncWorkspaceContext:
    """Context manager for temporary workspace switch (async)."""

    def __init__(self, client: AsyncCortexClient, workspace_id: UUID):
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


class _AsyncEnvironmentContext:
    """Context manager for temporary environment switch (async)."""

    def __init__(self, client: AsyncCortexClient, environment_id: UUID):
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
