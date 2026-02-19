"""
Metric variants handler - routes to direct or remote based on mode.

Provides unified interface for metric variant operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.variants import (
    MetricVariantCreateRequest,
    MetricVariantUpdateRequest,
    MetricVariantExecutionRequest
)
from cortex.sdk.schemas.responses.variants import (
    MetricVariantResponse,
    MetricVariantListResponse,
    MetricVariantExecutionResponse
)
from . import direct, remote


class MetricVariantsHandler:
    """
    Handler for metric variants operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = MetricVariantsHandler(mode=ConnectionMode.DIRECT)
        >>> variants = handler.list(environment_id=env_id)

        API mode:
        >>> handler = MetricVariantsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> variants = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize metric variants handler.

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
            operation: Operation name (e.g., "metric_variants.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="metric_variants",
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

    def create(self, request: MetricVariantCreateRequest) -> MetricVariantResponse:
        """
        Create a new metric variant.

        Args:
            request: Metric variant creation request

        Returns:
            Created metric variant response

        Examples:
            >>> from cortex.sdk.schemas.requests.variants import MetricVariantCreateRequest
            >>> from cortex.core.semantics.metrics.metric import MetricRef
            >>> request = MetricVariantCreateRequest(
            ...     environment_id=env_id,
            ...     name="my_variant",
            ...     source=MetricRef(metric_id=source_metric_id),
            ...     overrides=...
            ... )
            >>> variant = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="metric_variants.create",
            event_name=CortexEvents.METRIC_CREATED,
            func=lambda: (
                direct.create_variant(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_variant(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def list(
        self,
        environment_id: UUID,
        data_model_id: Optional[UUID] = None,
        source_metric_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> MetricVariantListResponse:
        """
        List metric variants with optional filtering.

        Args:
            environment_id: Environment ID
            data_model_id: Optional data model ID filter
            source_metric_id: Optional source metric ID filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of metric variant responses

        Examples:
            >>> variants = handler.list(environment_id=env_id)
            >>> # Filter by source metric
            >>> variants = handler.list(
            ...     environment_id=env_id,
            ...     source_metric_id=source_id
            ... )
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_variants(environment_id, data_model_id, source_metric_id, limit, offset)
        else:
            return remote.list_variants(
                    self.http_client, environment_id, data_model_id, source_metric_id, limit, offset
                )

    def get(self, variant_id: UUID, environment_id: UUID) -> MetricVariantResponse:
        """
        Get a metric variant by ID.

        Args:
            variant_id: Variant ID
            environment_id: Environment ID

        Returns:
            Metric variant response

        Examples:
            >>> variant = handler.get(variant_id, environment_id=env_id)
            >>> print(variant.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_variant(variant_id, environment_id)
        else:
            return remote.get_variant(self.http_client, variant_id, environment_id)

    def update(
        self, variant_id: UUID, request: MetricVariantUpdateRequest
    ) -> MetricVariantResponse:
        """
        Update a metric variant.

        Args:
            variant_id: Variant ID
            request: Update request

        Returns:
            Updated metric variant response

        Examples:
            >>> from cortex.sdk.schemas.requests.variants import MetricVariantUpdateRequest
            >>> request = MetricVariantUpdateRequest(
            ...     environment_id=env_id,
            ...     name="updated_name"
            ... )
            >>> variant = handler.update(variant_id, request)
        """
        return self._execute_with_hooks(
            operation="metric_variants.update",
            event_name=CortexEvents.METRIC_UPDATED,
            func=lambda: (
                direct.update_variant(variant_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_variant(self.http_client, variant_id, request)
            ),
            variant_id=variant_id,
            environment_id=request.environment_id,
        )

    def delete(self, variant_id: UUID, environment_id: UUID) -> None:
        """
        Delete a metric variant.

        Args:
            variant_id: Variant ID
            environment_id: Environment ID

        Examples:
            >>> handler.delete(variant_id, environment_id=env_id)
        """
        self._execute_with_hooks(
            operation="metric_variants.delete",
            event_name=CortexEvents.METRIC_DELETED,
            func=lambda: (
                direct.delete_variant(variant_id, environment_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_variant(self.http_client, variant_id, environment_id)
            ),
            variant_id=variant_id,
            environment_id=environment_id,
        )

    def reset(self, variant_id: UUID) -> Dict[str, Any]:
        """
        Reset a variant by removing all overrides.

        Args:
            variant_id: Variant ID

        Returns:
            Reset result dictionary

        Examples:
            >>> result = handler.reset(variant_id)
            >>> print(result["message"])
        """
        return self._execute_with_hooks(
            operation="metric_variants.reset",
            event_name=CortexEvents.METRIC_UPDATED,
            func=lambda: (
                direct.reset_variant(variant_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.reset_variant(self.http_client, variant_id)
            ),
            variant_id=variant_id,
        )

    def detach(self, variant_id: UUID) -> Dict[str, Any]:
        """
        Detach a variant by creating a new standalone metric.

        Args:
            variant_id: Variant ID

        Returns:
            Detach result dictionary with new metric ID

        Examples:
            >>> result = handler.detach(variant_id)
            >>> new_metric_id = result["data"]["id"]
        """
        return self._execute_with_hooks(
            operation="metric_variants.detach",
            event_name=CortexEvents.METRIC_CREATED,
            func=lambda: (
                direct.detach_variant(variant_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.detach_variant(self.http_client, variant_id)
            ),
            variant_id=variant_id,
        )

    def execute(
        self, variant_id: UUID, request: MetricVariantExecutionRequest
    ) -> MetricVariantExecutionResponse:
        """
        Execute a metric variant and return results.

        Args:
            variant_id: Variant ID
            request: Execution request

        Returns:
            Execution response with results

        Examples:
            >>> from cortex.sdk.schemas.requests.variants import MetricVariantExecutionRequest
            >>> request = MetricVariantExecutionRequest(
            ...     environment_id=env_id,
            ...     limit=100
            ... )
            >>> result = handler.execute(variant_id, request)
            >>> print(result.data)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_variant(variant_id, request)
        else:
            return remote.execute_variant(self.http_client, variant_id, request)

    def override_source(self, variant_id: UUID) -> Dict[str, Any]:
        """
        Override the source metric with the resolved state of this variant.

        WARNING: This modifies the source metric and cannot be undone!

        Args:
            variant_id: Variant ID

        Returns:
            Override result dictionary

        Examples:
            >>> result = handler.override_source(variant_id)
            >>> print(result["message"])
        """
        return self._execute_with_hooks(
            operation="metric_variants.override_source",
            event_name=CortexEvents.METRIC_UPDATED,
            func=lambda: (
                direct.override_source(variant_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.override_source(self.http_client, variant_id)
            ),
            variant_id=variant_id,
        )
