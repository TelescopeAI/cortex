"""
Metrics handler - routes to direct or remote based on mode.

Provides unified interface for metrics operations with hook integration.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import MetricsEventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
)
from cortex.sdk.schemas.requests.doctor import MetricDiagnoseRequest
from cortex.sdk.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
)
from cortex.sdk.schemas.responses.doctor import DiagnoseResponse
from . import direct, remote


class MetricsHandler:
    """
    Handler for metrics operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = MetricsHandler(mode=ConnectionMode.DIRECT)
        >>> metrics = handler.list(environment_id=env_id)

        API mode:
        >>> handler = MetricsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> metrics = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize metrics handler.

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
            operation: Operation name (e.g., "metrics.list")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = MetricsEventContext(
            operation=operation,
            manager="metrics",
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

    def list(
        self,
        environment_id: UUID,
        page: int = 1,
        page_size: int = 20,
        data_model_id: Optional[UUID] = None,
        public_only: Optional[bool] = None,
        valid_only: Optional[bool] = None
    ) -> MetricListResponse:
        """
        List metrics in an environment.

        Args:
            environment_id: Environment ID
            page: Page number (1-indexed, default: 1)
            page_size: Number of items per page (default: 20)
            data_model_id: Optional filter by data model ID
            public_only: Optional filter by public status
            valid_only: Optional filter by valid status

        Returns:
            MetricListResponse with list of metrics

        Examples:
            >>> metrics = handler.list(environment_id=env_id, page=1, page_size=10)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_metrics(
                environment_id, page, page_size,
                data_model_id, public_only, valid_only
            )
        else:
            return remote.list_metrics(
                self.http_client, environment_id, page, page_size,
                data_model_id, public_only, valid_only
            )

    def get(self, metric_id: UUID, environment_id: Optional[UUID] = None) -> MetricResponse:
        """
        Get a specific metric by ID.

        Args:
            metric_id: Metric ID
            environment_id: Optional environment ID

        Returns:
            MetricResponse

        Examples:
            >>> metric = handler.get(metric_id)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_metric(metric_id, environment_id)
        else:
            return remote.get_metric(self.http_client, metric_id, environment_id)

    def create(self, request: MetricCreateRequest) -> MetricResponse:
        """
        Create a new metric.

        Args:
            request: Metric creation request

        Returns:
            MetricResponse for created metric

        Examples:
            >>> request = MetricCreateRequest(name="Revenue", data_model_id=model_id)
            >>> metric = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="metrics.create",
            event_name=CortexEvents.METRIC_CREATED,
            func=lambda: (
                direct.create_metric(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_metric(self.http_client, request)
            ),
            data_model_id=request.data_model_id,
        )

    def update(self, metric_id: UUID, request: MetricUpdateRequest) -> MetricResponse:
        """
        Update a metric.

        Args:
            metric_id: Metric ID
            request: Metric update request

        Returns:
            MetricResponse for updated metric

        Examples:
            >>> request = MetricUpdateRequest(name="Updated Revenue")
            >>> metric = handler.update(metric_id, request)
        """
        return self._execute_with_hooks(
            operation="metrics.update",
            event_name=CortexEvents.METRIC_UPDATED,
            func=lambda: (
                direct.update_metric(metric_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_metric(self.http_client, metric_id, request)
            ),
            metric_id=metric_id,
        )

    def delete(self, metric_id: UUID, environment_id: Optional[UUID] = None) -> None:
        """
        Delete a metric.

        Args:
            metric_id: Metric ID
            environment_id: Optional environment ID

        Examples:
            >>> handler.delete(metric_id)
        """
        self._execute_with_hooks(
            operation="metrics.delete",
            event_name=CortexEvents.METRIC_DELETED,
            func=lambda: (
                direct.delete_metric(metric_id, environment_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_metric(self.http_client, metric_id, environment_id)
            ),
            metric_id=metric_id,
            environment_id=environment_id,
        )

    def execute(
        self, metric_id: UUID, request: MetricExecutionRequest
    ) -> MetricExecutionResponse:
        """
        Execute a metric query.

        Args:
            metric_id: Metric ID
            request: Execution request with parameters

        Returns:
            MetricExecutionResponse with query results

        Examples:
            >>> request = MetricExecutionRequest(
            ...     dimensions=["date"],
            ...     filters={"country": "US"}
            ... )
            >>> result = handler.execute(metric_id, request)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.execute_metric(metric_id, request)
        else:
            return remote.execute_metric(self.http_client, metric_id, request)

    def clone(self, metric_id: UUID, request: MetricCloneRequest) -> MetricResponse:
        """
        Clone a metric with a new name.

        Args:
            metric_id: Source metric ID
            request: Clone request with new name

        Returns:
            MetricResponse for cloned metric

        Examples:
            >>> request = MetricCloneRequest(new_name="Revenue (Copy)")
            >>> cloned = handler.clone(metric_id, request)
        """
        return self._execute_with_hooks(
            operation="metrics.clone",
            event_name=CortexEvents.METRIC_CLONED,
            func=lambda: (
                direct.clone_metric(metric_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.clone_metric(self.http_client, metric_id, request)
            ),
            metric_id=metric_id,
        )

    def list_versions(self, metric_id: UUID):
        """
        List all versions of a metric.

        Args:
            metric_id: Metric ID

        Returns:
            MetricVersionListResponse with list of versions

        Examples:
            >>> versions = handler.list_versions(metric_id)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_metric_versions(metric_id)
        else:
            return remote.list_metric_versions(self.http_client, metric_id)

    def create_version(self, metric_id: UUID, request):
        """
        Create a new version of a metric.

        Args:
            metric_id: Metric ID
            request: Version creation request

        Returns:
            MetricVersionResponse

        Examples:
            >>> from cortex.sdk.schemas.requests.metrics import MetricVersionCreateRequest
            >>> request = MetricVersionCreateRequest(description="Snapshot before Q4 changes")
            >>> version = handler.create_version(metric_id, request)
        """
        return self._execute_with_hooks(
            operation="metrics.create_version",
            event_name=CortexEvents.METRIC_UPDATED,
            func=lambda: (
                direct.create_metric_version(metric_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_metric_version(self.http_client, metric_id, request)
            ),
            metric_id=metric_id,
        )

    def generate_recommendations(self, request):
        """
        Generate metric recommendations from a data source schema.

        This analyzes the schema of a data source and generates a set of recommended
        metrics based on deterministic rules. The generated metrics are not saved.

        Args:
            request: Recommendations request

        Returns:
            MetricRecommendationsResponse with generated metrics

        Examples:
            >>> from cortex.sdk.schemas.requests.metrics import MetricRecommendationsRequest
            >>> request = MetricRecommendationsRequest(
            ...     environment_id=env_id,
            ...     data_source_id=ds_id,
            ...     data_model_id=dm_id
            ... )
            >>> recommendations = handler.generate_recommendations(request)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.generate_metric_recommendations(request)
        else:
            return remote.generate_metric_recommendations(self.http_client, request)

    def diagnose(self, request: MetricDiagnoseRequest) -> DiagnoseResponse:
        """
        Diagnose a metric for configuration issues.

        Runs through compilation, validation, SQL generation, and execution
        stages, collecting all errors and generating fix suggestions where possible.

        Args:
            request: Diagnose request with metric_id or inline metric

        Returns:
            DiagnoseResponse with healthy status and optional diagnosis
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.diagnose_metric(request)
        else:
            return remote.diagnose_metric(self.http_client, request)
