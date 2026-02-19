"""
Data sources handler - routes to direct or remote based on mode.

Provides unified interface for data source operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import DataSourcesEventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.data_sources import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceRebuildRequest
)
from cortex.sdk.schemas.responses.data_sources import (
    DataSourceResponse,
    DataSourceRebuildResponse
)
from . import direct, remote


class DataSourcesHandler:
    """
    Handler for data sources operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = DataSourcesHandler(mode=ConnectionMode.DIRECT)
        >>> sources = handler.list(environment_id=env_id)

        API mode:
        >>> handler = DataSourcesHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> sources = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize data sources handler.

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
            operation: Operation name (e.g., "data_sources.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = DataSourcesEventContext(
            operation=operation,
            manager="data_sources",
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

    def create(self, request: DataSourceCreateRequest) -> DataSourceResponse:
        """
        Create a new data source.

        Args:
            request: Data source creation request

        Returns:
            Created data source response

        Examples:
            >>> from cortex.sdk.schemas.requests.data_sources import DataSourceCreateRequest
            >>> request = DataSourceCreateRequest(
            ...     environment_id=env_id,
            ...     name="My Database",
            ...     alias="my_db",
            ...     source_catalog="default",
            ...     source_type="postgresql",
            ...     config={"host": "localhost", "port": 5432, ...}
            ... )
            >>> source = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="data_sources.create",
            event_name=CortexEvents.DATA_SOURCE_CREATED,
            func=lambda: (
                direct.create_data_source(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_data_source(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def get(self, data_source_id: UUID) -> DataSourceResponse:
        """
        Get a data source by ID.

        Args:
            data_source_id: Data source ID

        Returns:
            Data source response

        Examples:
            >>> source = handler.get(data_source_id)
            >>> print(source.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_data_source(data_source_id)
        else:
            return remote.get_data_source(self.http_client, data_source_id)

    def list(self, environment_id: UUID) -> List[DataSourceResponse]:
        """
        List all data sources in an environment.

        Args:
            environment_id: Environment ID

        Returns:
            List of data source responses

        Examples:
            >>> sources = handler.list(environment_id=env_id)
            >>> for source in sources:
            ...     print(source.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_data_sources(environment_id)
        else:
            return remote.list_data_sources(self.http_client, environment_id)

    def update(
        self, data_source_id: UUID, request: DataSourceUpdateRequest
    ) -> DataSourceResponse:
        """
        Update a data source.

        Args:
            data_source_id: Data source ID
            request: Update request

        Returns:
            Updated data source response

        Examples:
            >>> from cortex.sdk.schemas.requests.data_sources import DataSourceUpdateRequest
            >>> request = DataSourceUpdateRequest(name="Updated Name")
            >>> source = handler.update(data_source_id, request)
        """
        return self._execute_with_hooks(
            operation="data_sources.update",
            event_name=CortexEvents.DATA_SOURCE_UPDATED,
            func=lambda: (
                direct.update_data_source(data_source_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_data_source(self.http_client, data_source_id, request)
            ),
            data_source_id=data_source_id,
        )

    def delete(self, data_source_id: UUID, cascade: bool = False) -> None:
        """
        Delete a data source.

        Args:
            data_source_id: Data source ID
            cascade: If true, delete all dependent metrics (default: False)

        Examples:
            >>> handler.delete(data_source_id)
            >>> # With cascade to delete dependencies
            >>> handler.delete(data_source_id, cascade=True)
        """
        self._execute_with_hooks(
            operation="data_sources.delete",
            event_name=CortexEvents.DATA_SOURCE_DELETED,
            func=lambda: (
                direct.delete_data_source(data_source_id, cascade)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_data_source(self.http_client, data_source_id, cascade)
            ),
            data_source_id=data_source_id,
        )

    def ping(self, data_source_id: UUID) -> Dict[str, Any]:
        """
        Test connectivity to a data source.

        Args:
            data_source_id: Data source ID

        Returns:
            Ping result dictionary with status and message

        Examples:
            >>> result = handler.ping(data_source_id)
            >>> print(result["status"])  # "success" or "failed"
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.ping_data_source(data_source_id)
        else:
            return remote.ping_data_source(self.http_client, data_source_id)

    def get_schema(self, data_source_id: UUID) -> Dict[str, Any]:
        """
        Get the schema information for a data source.

        Args:
            data_source_id: Data source ID

        Returns:
            Schema information dictionary

        Examples:
            >>> schema = handler.get_schema(data_source_id)
            >>> print(schema["tables"])
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_data_source_schema(data_source_id)
        else:
            return remote.get_data_source_schema(self.http_client, data_source_id)

    def get_schema_humanized(self, data_source_id: UUID) -> Dict[str, Any]:
        """
        Get a human-readable description of the data source schema.

        Args:
            data_source_id: Data source ID

        Returns:
            Humanized schema information dictionary

        Examples:
            >>> schema = handler.get_schema_humanized(data_source_id)
            >>> print(schema["humanized_schema"])
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_data_source_schema_humanized(data_source_id)
        else:
            return remote.get_data_source_schema_humanized(
                self.http_client, data_source_id
            )

    def rebuild(
        self, data_source_id: UUID, request: DataSourceRebuildRequest = None
    ) -> DataSourceRebuildResponse:
        """
        Rebuild a spreadsheet data source from its original file.

        Args:
            data_source_id: Data source ID
            request: Rebuild request (optional, defaults to clear_cache=True)

        Returns:
            Rebuild response with updated metadata

        Examples:
            >>> from cortex.sdk.schemas.requests.data_sources import DataSourceRebuildRequest
            >>> request = DataSourceRebuildRequest(clear_cache=True)
            >>> result = handler.rebuild(data_source_id, request)
            >>> print(result.rebuilt_tables)
        """
        if request is None:
            request = DataSourceRebuildRequest()

        return self._execute_with_hooks(
            operation="data_sources.rebuild",
            event_name=CortexEvents.DATA_SOURCE_UPDATED,
            func=lambda: (
                direct.rebuild_data_source(data_source_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.rebuild_data_source(self.http_client, data_source_id, request)
            ),
            data_source_id=data_source_id,
        )

    def refresh(self, data_source_id: UUID) -> Dict[str, Any]:
        """
        Refresh a spreadsheet data source.

        Args:
            data_source_id: Data source ID

        Returns:
            Refresh result dictionary with refreshed/unchanged tables

        Examples:
            >>> result = handler.refresh(data_source_id)
            >>> print(result["refreshed_tables"])
        """
        return self._execute_with_hooks(
            operation="data_sources.refresh",
            event_name=CortexEvents.DATA_SOURCE_UPDATED,
            func=lambda: (
                direct.refresh_spreadsheet_source(data_source_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.refresh_spreadsheet_source(self.http_client, data_source_id)
            ),
            data_source_id=data_source_id,
        )

    def get_spreadsheet_status(self, data_source_id: UUID) -> Dict[str, Any]:
        """
        Get sync status and table list for a spreadsheet data source.

        Args:
            data_source_id: Data source ID

        Returns:
            Status information dictionary

        Examples:
            >>> status = handler.get_spreadsheet_status(data_source_id)
            >>> print(status["last_synced"])
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_spreadsheet_status(data_source_id)
        else:
            return remote.get_spreadsheet_status(self.http_client, data_source_id)
