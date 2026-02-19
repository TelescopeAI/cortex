"""
Pre-aggregations handler - routes to direct or remote based on mode.

Provides unified interface for pre-aggregation operations with hook integration.
"""
from typing import Optional, Dict, Any

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.core.preaggregations.models import PreAggregationSpec
from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest
from cortex.sdk.schemas.responses.preaggregations import (
    PreAggregationUpsertResponse,
    PreAggregationListResponse,
    PreAggregationStatusResponse
)
from . import direct, remote


class PreAggregationsHandler:
    """
    Handler for pre-aggregations operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = PreAggregationsHandler(mode=ConnectionMode.DIRECT)
        >>> specs = handler.list_preaggregation_specs()

        API mode:
        >>> handler = PreAggregationsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> specs = handler.list_preaggregation_specs()
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize pre-aggregations handler.

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
            operation: Operation name (e.g., "preaggregations.upsert")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="preaggregations",
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

    def upsert_preaggregation_spec(
        self, request: PreAggregationUpsertRequest
    ) -> PreAggregationUpsertResponse:
        """
        Create or update a pre-aggregation spec.

        Args:
            request: Pre-aggregation upsert request

        Returns:
            Upsert response

        Examples:
            >>> from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest
            >>> request = PreAggregationUpsertRequest(
            ...     spec_id="daily_sales",
            ...     metric_id=metric_id,
            ...     dimensions=["date", "product"],
            ...     measures=["revenue", "quantity"]
            ... )
            >>> response = handler.upsert_preaggregation_spec(request)
        """
        return self._execute_with_hooks(
            operation="preaggregations.upsert_spec",
            event_name=CortexEvents.PREAGGREGATION_CREATED,
            func=lambda: (
                direct.upsert_preaggregation_spec(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.upsert_preaggregation_spec(self.http_client, request)
            ),
        )

    def list_preaggregation_specs(
        self, metric_id: Optional[str] = None
    ) -> PreAggregationListResponse:
        """
        List pre-aggregation specs with optional metric filtering.

        Args:
            metric_id: Optional metric ID to filter by

        Returns:
            List of pre-aggregation specs

        Examples:
            >>> specs = handler.list_preaggregation_specs()
            >>> for spec in specs.specs:
            ...     print(spec.spec_id)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_preaggregation_specs(metric_id)
        else:
            return remote.list_preaggregation_specs(self.http_client, metric_id)

    def get_preaggregation_spec(self, spec_id: str) -> PreAggregationSpec:
        """
        Get a pre-aggregation spec by ID.

        Args:
            spec_id: Pre-aggregation spec ID

        Returns:
            Pre-aggregation spec

        Examples:
            >>> spec = handler.get_preaggregation_spec("daily_sales")
            >>> print(spec.dimensions)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_preaggregation_spec(spec_id)
        else:
            return remote.get_preaggregation_spec(self.http_client, spec_id)

    def refresh_preaggregation_spec(
        self, spec_id: str, dry_run: bool = False
    ) -> PreAggregationStatusResponse:
        """
        Build or refresh a pre-aggregation spec.

        Args:
            spec_id: Pre-aggregation spec ID
            dry_run: If True, only validate without building

        Returns:
            Status response

        Examples:
            >>> # Build pre-aggregation
            >>> status = handler.refresh_preaggregation_spec("daily_sales")
            >>> print(status.status)

            >>> # Dry run to validate
            >>> status = handler.refresh_preaggregation_spec("daily_sales", dry_run=True)
        """
        return self._execute_with_hooks(
            operation="preaggregations.refresh_spec",
            event_name=CortexEvents.PREAGGREGATION_REFRESHED,
            func=lambda: (
                direct.refresh_preaggregation_spec(spec_id, dry_run)
                if self.mode == ConnectionMode.DIRECT
                else remote.refresh_preaggregation_spec(self.http_client, spec_id, dry_run)
            ),
            spec_id=spec_id,
            dry_run=dry_run,
        )

    def get_preaggregation_status(self, spec_id: str) -> PreAggregationStatusResponse:
        """
        Get pre-aggregation spec status.

        Args:
            spec_id: Pre-aggregation spec ID

        Returns:
            Status response

        Examples:
            >>> status = handler.get_preaggregation_status("daily_sales")
            >>> print(status.status.error if status.status.error else "No errors")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_preaggregation_status(spec_id)
        else:
            return remote.get_preaggregation_status(self.http_client, spec_id)

    def delete_preaggregation_spec(self, spec_id: str) -> dict:
        """
        Delete a pre-aggregation spec.

        Args:
            spec_id: Pre-aggregation spec ID

        Returns:
            Success message

        Examples:
            >>> result = handler.delete_preaggregation_spec("daily_sales")
            >>> print(result)
        """
        return self._execute_with_hooks(
            operation="preaggregations.delete_spec",
            event_name=CortexEvents.PREAGGREGATION_DELETED,
            func=lambda: (
                direct.delete_preaggregation_spec(spec_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_preaggregation_spec(self.http_client, spec_id)
            ),
            spec_id=spec_id,
        )
