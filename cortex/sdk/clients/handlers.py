"""
Handler loader for dynamic handler initialization.

Provides centralized handler registry and loading, avoiding circular dependencies.
"""
from typing import Dict, Any, Optional

from cortex.sdk.config import ConnectionMode
from cortex.sdk.hooks.manager import HookManager

# Import all handler classes
from cortex.sdk.handlers.metrics.base import MetricsHandler
from cortex.sdk.handlers.file_storage.base import FileStorageHandler
from cortex.sdk.handlers.data_sources.base import DataSourcesHandler
from cortex.sdk.handlers.metric_variants.base import MetricVariantsHandler
from cortex.sdk.handlers.data_models.base import DataModelsHandler
from cortex.sdk.handlers.dashboards.base import DashboardsHandler
from cortex.sdk.handlers.workspaces.base import WorkspacesHandler
from cortex.sdk.handlers.environments.base import EnvironmentsHandler
from cortex.sdk.handlers.consumers.base import ConsumersHandler
from cortex.sdk.handlers.consumer_groups.base import ConsumerGroupsHandler

from cortex.sdk.handlers.query_history.base import QueryHistoryHandler
from cortex.sdk.handlers.preaggregations.base import PreAggregationsHandler
from cortex.sdk.handlers.admin.base import AdminHandler


# Handler registry with enable/disable capability
# Pattern inspired by cortex/api/routers/__init__.py
HANDLERS = [
    {"name": "metrics", "handler": MetricsHandler, "enabled": True},
    {"name": "file_storage", "handler": FileStorageHandler, "enabled": True},
    {"name": "data_sources", "handler": DataSourcesHandler, "enabled": True},
    {"name": "metric_variants", "handler": MetricVariantsHandler, "enabled": True},
    {"name": "data_models", "handler": DataModelsHandler, "enabled": True},
    {"name": "dashboards", "handler": DashboardsHandler, "enabled": True},
    {"name": "workspaces", "handler": WorkspacesHandler, "enabled": True},
    {"name": "environments", "handler": EnvironmentsHandler, "enabled": True},
    {"name": "consumers", "handler": ConsumersHandler, "enabled": True},
    {"name": "consumer_groups", "handler": ConsumerGroupsHandler, "enabled": True},
    {"name": "query_history", "handler": QueryHistoryHandler, "enabled": True},
    {"name": "preaggregations", "handler": PreAggregationsHandler, "enabled": True},
    {"name": "admin", "handler": AdminHandler, "enabled": True},
]

ENABLED_HANDLERS = list(filter(lambda h: h["enabled"] is True, HANDLERS))


class CortexHandlerLoader:
    """
    Dynamic handler loader - avoids circular dependencies.

    Client imports this loader, loader imports handler classes.
    Handlers are loaded at runtime based on configuration.

    Examples:
        >>> handlers = CortexHandlerLoader.load_handlers(
        ...     mode=ConnectionMode.DIRECT,
        ...     http_client=None,
        ...     hooks=hook_manager,
        ...     client_context={"workspace_id": ws_id, "environment_id": env_id}
        ... )
        >>> # handlers is a dict: {"metrics": MetricsHandler(...), ...}
    """

    @staticmethod
    def load_handlers(
        mode: ConnectionMode,
        http_client: Optional[Any],
        hooks: HookManager,
        client_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Load and initialize all enabled handlers.

        Args:
            mode: Connection mode (DIRECT or API)
            http_client: HTTP client instance (for API mode, None for DIRECT)
            hooks: Hook manager for event emission
            client_context: Client context (workspace_id, environment_id, etc.)

        Returns:
            Dictionary mapping handler names to handler instances

        Examples:
            >>> from cortex.sdk.config import ConnectionMode
            >>> from cortex.sdk.hooks.manager import HookManager
            >>>
            >>> handlers = CortexHandlerLoader.load_handlers(
            ...     mode=ConnectionMode.DIRECT,
            ...     http_client=None,
            ...     hooks=HookManager(),
            ...     client_context={}
            ... )
            >>> print(handlers.keys())  # ['metrics', ...]
        """
        handlers = {}

        for handler_config in ENABLED_HANDLERS:
            handler_class = handler_config["handler"]
            handler_name = handler_config["name"]

            # Initialize handler with standard parameters
            handlers[handler_name] = handler_class(
                mode=mode,
                http_client=http_client,
                hooks=hooks,
                client_context=client_context,
            )

        return handlers
