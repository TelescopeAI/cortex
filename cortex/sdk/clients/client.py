"""
Main Cortex SDK client.

Provides unified interface to all Cortex operations through handlers.
"""
from typing import Optional, List, Union
from uuid import UUID
import logging

from cortex.sdk.config import CortexSDKSettings, ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
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


class CortexClient:
    """
    Main Cortex SDK client for all operations.

    Provides unified access to all Cortex resources through handlers.
    Supports two connection modes:
    - **Direct mode**: Local Core service access (default)
    - **API mode**: HTTP client to remote Cortex API server

    Attributes:
        workspace_id: Current workspace ID context
        environment_id: Current environment ID context
        hooks: Hook manager for dynamic hook management
        metrics: Metrics handler
        (... other handlers as they're implemented)

    Examples:
        Direct mode (local):
        >>> client = CortexClient(mode="direct")
        >>> metrics = client.metrics.list(environment_id=env_id)

        API mode (remote server):
        >>> client = CortexClient(
        ...     mode="api",
        ...     host="http://localhost:9002/api/v1",
        ...     api_key="your-api-key"
        ... )
        >>> metrics = client.metrics.list(environment_id=env_id)

        With context:
        >>> client = CortexClient(
        ...     mode="direct",
        ...     workspace_id=workspace_id,
        ...     environment_id=env_id
        ... )
        >>> metrics = client.metrics.list()  # Uses env_id from client

        With hooks:
        >>> from cortex.sdk.hooks.builtin import LoggingHook
        >>> client = CortexClient(
        ...     mode="direct",
        ...     hooks=[LoggingHook()]
        ... )

        Context manager:
        >>> with CortexClient(mode="direct") as client:
        ...     metrics = client.metrics.list(environment_id=env_id)
        # Auto-cleanup
    """

    # Handler attributes (type-hinted for IDE support)
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
        Initialize Cortex SDK client.

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
            >>> client = CortexClient()  # Direct mode
            >>> client = CortexClient(
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

        # Create HTTP client if in API mode
        self._http_client = None
        if self._settings.mode == ConnectionMode.API:
            if not self._settings.host:
                raise ValueError("host is required for API mode")

            logger.info(f"Initializing API mode: {self._settings.host}")
            self._http_client = CortexHTTPClient(
                host=self._settings.host,
                auth_provider=auth_provider,
                timeout=self._settings.timeout,
                max_retries=self._settings.max_retries,
            )
        else:
            logger.info("Initializing Direct mode")

        # Initialize handlers
        self._init_handlers()

    def _init_handlers(self):
        """Initialize all handlers explicitly."""
        # Prepare context for handlers
        client_context = {
            "workspace_id": self._workspace_id,
            "environment_id": self._environment_id,
        }

        logger.debug("Initializing handlers...")

        # Initialize each handler explicitly
        self.metrics = MetricsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.metric_variants = MetricVariantsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.data_sources = DataSourcesHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.file_storage = FileStorageHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.data_models = DataModelsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.dashboards = DashboardsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.workspaces = WorkspacesHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.environments = EnvironmentsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.consumers = ConsumersHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.consumer_groups = ConsumerGroupsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.query_history = QueryHistoryHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.preaggregations = PreAggregationsHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        self.admin = AdminHandler(
            mode=self._settings.mode,
            http_client=self._http_client,
            hooks=self._hooks,
            client_context=client_context,
        )

        logger.debug("All handlers initialized")

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
            >>> metrics = client.metrics.list()  # Uses this environment_id
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
            ...     metrics = client.metrics.list()  # Uses prod_env_id
            # Back to original environment_id
        """
        return _EnvironmentContext(self, environment_id)

    def close(self):
        """
        Close client and clean up resources.

        Examples:
            >>> client.close()

            With context manager:
            >>> with CortexClient() as client:
            ...     metrics = client.metrics.list(environment_id=env_id)
            # Auto-cleanup
        """
        logger.debug("Closing Cortex client")
        if self._http_client:
            self._http_client.close()

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
