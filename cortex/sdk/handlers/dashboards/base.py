"""
Dashboards handler - routes to direct or remote based on mode.

Provides unified interface for dashboard operations with hook integration.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.dashboards import (
    DashboardCreateRequest,
    DashboardUpdateRequest,
    SetDefaultViewRequest
)
from cortex.sdk.schemas.responses.dashboards import (
    DashboardResponse,
    DashboardListResponse,
    DashboardExecutionResponse,
    DashboardViewExecutionResponse,
    WidgetExecutionResponse
)
from . import direct, remote


class DashboardsHandler:
    """
    Handler for dashboards operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = DashboardsHandler(mode=ConnectionMode.DIRECT)
        >>> dashboards = handler.list(environment_id=env_id)

        API mode:
        >>> handler = DashboardsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> dashboards = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize dashboards handler.

        Args:
            mode: Connection mode (DIRECT or API)
            http_client: HTTP client instance (required for API mode)
            hooks: Hook manager for event emission
            client_context: Client context (workspace_id, environment_id)
        """
        self.mode = mode
        self.http_client = http_client
        self._hooks = hooks or HookManager()
        self._context = client_context or {}

    def _execute_with_hooks(
        self, operation: str, event_name: CortexEvents, func, **context_kwargs
    ):
        """
        Execute operation with hook lifecycle.

        Emits BEFORE → operation → AFTER (or ERROR) events.

        Args:
            operation: Operation name (e.g., "dashboards.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="dashboards",
            action=operation.split(".")[-1],
            event_type=HookEventType.BEFORE,
            event_name=event_name,
            params=context_kwargs,
            **context_kwargs,
        )
        context = self._hooks.emit_event(context)

        try:
            # Execute operation
            result = func()

            # AFTER hook
            context.event_type = HookEventType.AFTER
            context.result = result
            self._hooks.emit_event(context)

            return result
        except Exception as e:
            # ERROR hook
            context.event_type = HookEventType.ERROR
            context.error = e
            self._hooks.emit_event(context)
            raise

    def create(self, request: DashboardCreateRequest) -> DashboardResponse:
        """
        Create a new dashboard.

        Args:
            request: Dashboard creation request

        Returns:
            Created dashboard response

        Examples:
            >>> from cortex.sdk.schemas.requests.dashboards import DashboardCreateRequest
            >>> request = DashboardCreateRequest(
            ...     environment_id=env_id,
            ...     name="Sales Dashboard",
            ...     type=DashboardType.OPERATIONAL
            ... )
            >>> dashboard = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="dashboards.create",
            event_name=CortexEvents.DASHBOARD_CREATED,
            func=lambda: (
                direct.create_dashboard(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_dashboard(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def get(self, dashboard_id: UUID) -> DashboardResponse:
        """
        Get a dashboard by ID.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Dashboard response

        Examples:
            >>> dashboard = handler.get(dashboard_id)
            >>> print(dashboard.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_dashboard(dashboard_id)
        else:
            return remote.get_dashboard(self.http_client, dashboard_id)

    def list(self, environment_id: UUID) -> DashboardListResponse:
        """
        List dashboards in an environment.

        Args:
            environment_id: Environment ID

        Returns:
            List of dashboard responses

        Examples:
            >>> dashboards = handler.list(environment_id=env_id)
            >>> for dashboard in dashboards.dashboards:
            ...     print(dashboard.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_dashboards(environment_id)
        else:
            return remote.list_dashboards(self.http_client, environment_id)

    def update(
        self, dashboard_id: UUID, request: DashboardUpdateRequest
    ) -> DashboardResponse:
        """
        Update a dashboard.

        Args:
            dashboard_id: Dashboard ID
            request: Update request

        Returns:
            Updated dashboard response

        Examples:
            >>> from cortex.sdk.schemas.requests.dashboards import DashboardUpdateRequest
            >>> request = DashboardUpdateRequest(
            ...     name="Updated Dashboard",
            ...     description="Updated description"
            ... )
            >>> dashboard = handler.update(dashboard_id, request)
        """
        return self._execute_with_hooks(
            operation="dashboards.update",
            event_name=CortexEvents.DASHBOARD_UPDATED,
            func=lambda: (
                direct.update_dashboard(dashboard_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_dashboard(self.http_client, dashboard_id, request)
            ),
            dashboard_id=dashboard_id,
        )

    def delete(self, dashboard_id: UUID) -> None:
        """
        Delete a dashboard.

        Args:
            dashboard_id: Dashboard ID

        Examples:
            >>> handler.delete(dashboard_id)
        """
        self._execute_with_hooks(
            operation="dashboards.delete",
            event_name=CortexEvents.DASHBOARD_DELETED,
            func=lambda: (
                direct.delete_dashboard(dashboard_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_dashboard(self.http_client, dashboard_id)
            ),
            dashboard_id=dashboard_id,
        )

    def set_default_view(
        self, dashboard_id: UUID, request: SetDefaultViewRequest
    ) -> DashboardResponse:
        """
        Set default view for a dashboard.

        Args:
            dashboard_id: Dashboard ID
            request: Set default view request

        Returns:
            Updated dashboard response

        Examples:
            >>> from cortex.sdk.schemas.requests.dashboards import SetDefaultViewRequest
            >>> request = SetDefaultViewRequest(view_alias="overview")
            >>> dashboard = handler.set_default_view(dashboard_id, request)
        """
        return self._execute_with_hooks(
            operation="dashboards.set_default_view",
            event_name=CortexEvents.DASHBOARD_UPDATED,
            func=lambda: (
                direct.set_default_view(dashboard_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.set_default_view(self.http_client, dashboard_id, request)
            ),
            dashboard_id=dashboard_id,
        )

    def execute(
        self, dashboard_id: UUID, view_alias: Optional[str] = None
    ) -> DashboardExecutionResponse:
        """
        Execute a dashboard.

        Args:
            dashboard_id: Dashboard ID
            view_alias: Optional specific view to execute

        Returns:
            Dashboard execution response

        Examples:
            >>> result = handler.execute(dashboard_id)
            >>> print(result.total_execution_time_ms)

            Execute specific view:
            >>> result = handler.execute(dashboard_id, view_alias="overview")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_dashboard(dashboard_id, view_alias)
        else:
            return remote.execute_dashboard(self.http_client, dashboard_id, view_alias)

    def execute_view(
        self, dashboard_id: UUID, view_alias: str
    ) -> DashboardViewExecutionResponse:
        """
        Execute a specific dashboard view.

        Args:
            dashboard_id: Dashboard ID
            view_alias: View alias

        Returns:
            Dashboard view execution response

        Examples:
            >>> result = handler.execute_view(dashboard_id, "overview")
            >>> for widget in result.widgets:
            ...     print(widget.widget_alias)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_dashboard_view(dashboard_id, view_alias)
        else:
            return remote.execute_dashboard_view(self.http_client, dashboard_id, view_alias)

    def execute_widget(
        self, dashboard_id: UUID, view_alias: str, widget_alias: str
    ) -> WidgetExecutionResponse:
        """
        Execute a specific widget.

        Args:
            dashboard_id: Dashboard ID
            view_alias: View alias
            widget_alias: Widget alias

        Returns:
            Widget execution response

        Examples:
            >>> result = handler.execute_widget(dashboard_id, "overview", "revenue_chart")
            >>> print(result.data)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_widget(dashboard_id, view_alias, widget_alias)
        else:
            return remote.execute_widget(self.http_client, dashboard_id, view_alias, widget_alias)

    def delete_widget(
        self, dashboard_id: UUID, view_alias: str, widget_alias: str
    ) -> DashboardResponse:
        """
        Delete a widget from a dashboard view.

        Args:
            dashboard_id: Dashboard ID
            view_alias: View alias
            widget_alias: Widget alias

        Returns:
            Updated dashboard response

        Examples:
            >>> dashboard = handler.delete_widget(dashboard_id, "overview", "revenue_chart")
        """
        return self._execute_with_hooks(
            operation="dashboards.delete_widget",
            event_name=CortexEvents.DASHBOARD_UPDATED,
            func=lambda: (
                direct.delete_widget(dashboard_id, view_alias, widget_alias)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_widget(self.http_client, dashboard_id, view_alias, widget_alias)
            ),
            dashboard_id=dashboard_id,
        )

    def preview(
        self, dashboard_id: UUID, config: DashboardUpdateRequest
    ) -> DashboardExecutionResponse:
        """
        Preview dashboard execution without saving.

        Args:
            dashboard_id: Dashboard ID
            config: Dashboard configuration for preview

        Returns:
            Dashboard execution response

        Examples:
            >>> from cortex.sdk.schemas.requests.dashboards import DashboardUpdateRequest
            >>> config = DashboardUpdateRequest(views=[...])
            >>> result = handler.preview(dashboard_id, config)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.preview_dashboard(dashboard_id, config)
        else:
            return remote.preview_dashboard(self.http_client, dashboard_id, config)
