"""
Query history handler - routes to direct or remote based on mode.

Provides unified interface for query history operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.query_history import (
    QueryHistoryFilterRequest,
    QueryHistoryStatsRequest,
    SlowQueriesRequest,
    ClearQueryHistoryRequest
)
from cortex.sdk.schemas.responses.query_history import (
    QueryLogResponse,
    QueryLogListResponse,
    ExecutionStatsResponse,
    SlowQueryResponse
)
from . import direct, remote


class QueryHistoryHandler:
    """
    Handler for query history operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = QueryHistoryHandler(mode=ConnectionMode.DIRECT)
        >>> logs = handler.get_query_history(filter_request)

        API mode:
        >>> handler = QueryHistoryHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> logs = handler.get_query_history(filter_request)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize query history handler.

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
            operation: Operation name (e.g., "query_history.get")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="query_history",
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

    def get_query_history(self, request: QueryHistoryFilterRequest) -> QueryLogListResponse:
        """
        Get query history with optional filtering.

        Args:
            request: Query history filter request

        Returns:
            Query log list response

        Examples:
            >>> from cortex.sdk.schemas.requests.query_history import QueryHistoryFilterRequest
            >>> request = QueryHistoryFilterRequest(
            ...     metric_id=metric_id,
            ...     success=True,
            ...     limit=50
            ... )
            >>> logs = handler.get_query_history(request)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_query_history(request)
        else:
            return remote.get_query_history(self.http_client, request)

    def get_query_log(self, query_id: UUID) -> QueryLogResponse:
        """
        Get a specific query log by ID.

        Args:
            query_id: Query log ID

        Returns:
            Query log response

        Examples:
            >>> log = handler.get_query_log(query_id)
            >>> print(log.query)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_query_log(query_id)
        else:
            return remote.get_query_log(self.http_client, query_id)

    def get_execution_stats(self, request: QueryHistoryStatsRequest) -> ExecutionStatsResponse:
        """
        Get aggregated execution statistics.

        Args:
            request: Query history stats request

        Returns:
            Execution stats response

        Examples:
            >>> from cortex.sdk.schemas.requests.query_history import QueryHistoryStatsRequest
            >>> request = QueryHistoryStatsRequest(
            ...     metric_id=metric_id,
            ...     time_range="24h"
            ... )
            >>> stats = handler.get_execution_stats(request)
            >>> print(f"Success rate: {stats.success_rate}")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_execution_stats(request)
        else:
            return remote.get_execution_stats(self.http_client, request)

    def get_slow_queries(self, request: SlowQueriesRequest) -> List[SlowQueryResponse]:
        """
        Get slowest queries for performance analysis.

        Args:
            request: Slow queries request

        Returns:
            List of slow query responses

        Examples:
            >>> from cortex.sdk.schemas.requests.query_history import SlowQueriesRequest
            >>> request = SlowQueriesRequest(
            ...     limit=10,
            ...     threshold_ms=1000.0,
            ...     time_range="7d"
            ... )
            >>> slow_queries = handler.get_slow_queries(request)
            >>> for query in slow_queries:
            ...     print(f"Duration: {query.duration}ms")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_slow_queries(request)
        else:
            return remote.get_slow_queries(self.http_client, request)

    def clear_query_history(self, request: ClearQueryHistoryRequest) -> dict:
        """
        Clear query history with optional time-based filtering (admin only).

        Args:
            request: Clear query history request

        Returns:
            Success message with count

        Examples:
            >>> from cortex.sdk.schemas.requests.query_history import ClearQueryHistoryRequest
            >>> from datetime import datetime, timedelta
            >>> request = ClearQueryHistoryRequest(
            ...     older_than=datetime.now() - timedelta(days=30)
            ... )
            >>> result = handler.clear_query_history(request)
            >>> print(f"Deleted {result['deleted_count']} entries")
        """
        return self._execute_with_hooks(
            operation="query_history.clear_query_history",
            event_name=CortexEvents.QUERY_EXECUTED,
            func=lambda: (
                direct.clear_query_history(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.clear_query_history(self.http_client, request)
            ),
        )
