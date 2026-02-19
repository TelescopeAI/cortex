"""
Metrics manager for metric operations.

Handles CRUD operations, execution, compilation, and cloning of semantic metrics.
"""
from typing import Any, Dict, List, Optional
from uuid import UUID
import logging

from cortex.sdk.managers.base import BaseManager
from cortex.sdk.hooks.contexts import MetricsEventContext
from cortex.sdk.events.types import CortexEvents
from cortex.sdk.exceptions.base import CortexValidationError

logger = logging.getLogger(__name__)


class MetricsManager(BaseManager):
    """
    Manager for semantic metric operations.

    Provides comprehensive metric management including:
    - CRUD operations (create, read, update, delete)
    - Metric execution with query parameters
    - Metric compilation (SQL generation)
    - Metric cloning

    All operations integrate with hooks system for logging, metrics collection,
    and custom behavior.

    Examples:
        List metrics:
        >>> client = CortexClient(mode="direct", environment_id=env_id)
        >>> metrics = client.metrics.list()

        Create metric:
        >>> metric = client.metrics.create(
        ...     MetricCreate(
        ...         name="Revenue",
        ...         data_model_id=model_id,
        ...         measures=[...],
        ...         dimensions=[...]
        ...     )
        ... )

        Execute metric:
        >>> result = client.metrics.execute(
        ...     metric_id,
        ...     QueryParams(
        ...         dimensions=["date"],
        ...         filters={"country": "US"}
        ...     )
        ... )
    """

    def list(
        self, environment_id: Optional[UUID] = None, **filters
    ) -> Dict[str, Any]:
        """
        List all metrics in an environment.

        Args:
            environment_id: Optional override (uses client context if not provided)
            **filters: Additional filters including:
                - page (int): Page number (default: 1)
                - page_size (int): Items per page (default: 20)
                - data_model_id (UUID): Filter by data model
                - public_only (bool): Filter by public status
                - valid_only (bool): Filter by valid status

        Returns:
            Paginated list of metrics with total_count, page, and page_size

        Raises:
            CortexValidationError: If environment_id not provided and not in client context

        Examples:
            >>> metrics = client.metrics.list()
            >>> metrics = client.metrics.list(environment_id=other_env_id)
            >>> metrics = client.metrics.list(page=1, page_size=10)
            >>> metrics = client.metrics.list(data_model_id=model_id, public_only=True)
        """
        env_id = environment_id or self.environment_id
        if not env_id:
            raise CortexValidationError(
                "environment_id required (set on client or pass as parameter)"
            )

        return self._execute_with_hooks(
            operation="metrics.list",
            event_name=CortexEvents.METRIC_LISTED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.get(
                "/metrics", params={"environment_id": str(env_id), **filters}
            ),
            environment_id=env_id,
        )

    def get(
        self, metric_id: UUID, environment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get a specific metric by ID.

        Args:
            metric_id: Metric ID
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Metric data

        Raises:
            CortexNotFoundError: If metric doesn't exist
            CortexValidationError: If environment_id not provided

        Examples:
            >>> metric = client.metrics.get(metric_id)
            >>> metric = client.metrics.get(metric_id, environment_id=other_env_id)
        """
        env_id = environment_id or self.environment_id

        return self._execute_with_hooks(
            operation="metrics.get",
            event_name=CortexEvents.METRIC_RETRIEVED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.get(
                f"/metrics/{metric_id}",
                params={"environment_id": str(env_id)} if env_id else None,
            ),
            metric_id=metric_id,
            environment_id=env_id,
        )

    def create(
        self, metric: Dict[str, Any], environment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create a new metric.

        Args:
            metric: Metric configuration (MetricCreate schema)
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Created metric

        Raises:
            CortexValidationError: If validation fails

        Examples:
            >>> metric = client.metrics.create({
            ...     "name": "Revenue",
            ...     "data_model_id": str(model_id),
            ...     "measures": [{
            ...         "name": "Total Revenue",
            ...         "aggregation": "sum",
            ...         "field": "amount"
            ...     }],
            ...     "dimensions": [{"name": "date", "field": "order_date"}]
            ... })
        """
        env_id = environment_id or self.environment_id
        if not env_id:
            raise CortexValidationError("environment_id required")

        # Add environment_id to metric data
        metric_data = {**metric, "environment_id": str(env_id)}

        return self._execute_with_hooks(
            operation="metrics.create",
            event_name=CortexEvents.METRIC_CREATED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.post("/metrics", data=metric_data),
            environment_id=env_id,
            data_model_id=metric.get("data_model_id"),
        )

    def update(
        self,
        metric_id: UUID,
        updates: Dict[str, Any],
        environment_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Update a metric.

        Args:
            metric_id: Metric ID
            updates: Fields to update (MetricUpdate schema)
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Updated metric

        Raises:
            CortexNotFoundError: If metric doesn't exist
            CortexValidationError: If validation fails

        Examples:
            >>> metric = client.metrics.update(
            ...     metric_id,
            ...     {"name": "Total Revenue (Updated)"}
            ... )
        """
        env_id = environment_id or self.environment_id

        # Add environment_id to updates
        update_data = {**updates}
        if env_id:
            update_data["environment_id"] = str(env_id)

        return self._execute_with_hooks(
            operation="metrics.update",
            event_name=CortexEvents.METRIC_UPDATED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.put(f"/metrics/{metric_id}", data=update_data),
            metric_id=metric_id,
            environment_id=env_id,
        )

    def delete(
        self, metric_id: UUID, environment_id: Optional[UUID] = None
    ) -> None:
        """
        Delete a metric.

        Args:
            metric_id: Metric ID
            environment_id: Optional override (uses client context if not provided)

        Raises:
            CortexNotFoundError: If metric doesn't exist

        Examples:
            >>> client.metrics.delete(metric_id)
        """
        env_id = environment_id or self.environment_id

        self._execute_with_hooks(
            operation="metrics.delete",
            event_name=CortexEvents.METRIC_DELETED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.delete(
                f"/metrics/{metric_id}",
                params={"environment_id": str(env_id)} if env_id else None,
            ),
            metric_id=metric_id,
            environment_id=env_id,
        )

    def execute(
        self,
        metric_id: UUID,
        params: Optional[Dict[str, Any]] = None,
        environment_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Execute a metric query.

        Args:
            metric_id: Metric ID
            params: Query parameters (dimensions, filters, limit, etc.)
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Query result with data and metadata

        Examples:
            >>> result = client.metrics.execute(metric_id)
            >>> result = client.metrics.execute(
            ...     metric_id,
            ...     params={
            ...         "dimensions": ["date", "country"],
            ...         "filters": {"country": "US"},
            ...         "limit": 100
            ...     }
            ... )
        """
        env_id = environment_id or self.environment_id

        query_params = params or {}
        if env_id:
            query_params["environment_id"] = str(env_id)

        return self._execute_with_hooks(
            operation="metrics.execute",
            event_name=CortexEvents.METRIC_EXECUTED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.post(
                f"/metrics/{metric_id}/execute", data=query_params
            ),
            metric_id=metric_id,
            environment_id=env_id,
        )

    def compile(
        self, metric_id: UUID, environment_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Compile metric to SQL.

        Args:
            metric_id: Metric ID
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Compiled metric with SQL

        Examples:
            >>> compiled = client.metrics.compile(metric_id)
            >>> print(compiled["sql"])
        """
        env_id = environment_id or self.environment_id

        return self._execute_with_hooks(
            operation="metrics.compile",
            event_name=CortexEvents.METRIC_COMPILED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.post(
                f"/metrics/{metric_id}/compile",
                data={"environment_id": str(env_id)} if env_id else {},
            ),
            metric_id=metric_id,
            environment_id=env_id,
        )

    def clone(
        self,
        metric_id: UUID,
        new_name: str,
        environment_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Clone a metric with a new name.

        Args:
            metric_id: Source metric ID
            new_name: Name for cloned metric
            environment_id: Optional override (uses client context if not provided)

        Returns:
            Cloned metric

        Examples:
            >>> cloned = client.metrics.clone(metric_id, "Revenue (Copy)")
        """
        env_id = environment_id or self.environment_id

        return self._execute_with_hooks(
            operation="metrics.clone",
            event_name=CortexEvents.METRIC_CLONED,
            event_context_class=MetricsEventContext,
            func=lambda: self._transport.post(
                f"/metrics/{metric_id}/clone",
                data={"new_name": new_name, "environment_id": str(env_id) if env_id else None},
            ),
            metric_id=metric_id,
            environment_id=env_id,
        )
