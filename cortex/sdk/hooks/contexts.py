"""
Event context models for hooks.

Uses TSModel (not BaseModel) per Cortex standards.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.sdk.events.types import CortexEvents, HookEventType


class EventContext(TSModel):
    """
    Context passed to hooks for every event.

    IMPORTANT: Uses TSModel, not BaseModel!

    Attributes:
        operation: Operation name (e.g., "metrics.create")
        manager: Manager name (e.g., "metrics")
        action: Action name (e.g., "create")
        event_type: Event type (BEFORE, AFTER, ERROR)
        event_name: Specific event (METRIC_CREATED, etc.)
        params: Operation parameters
        result: Operation result (AFTER events only)
        error: Exception (ERROR events only)
        metadata: Additional context data

    Examples:
        >>> context = EventContext(
        ...     operation="metrics.create",
        ...     manager="metrics",
        ...     action="create",
        ...     event_type=HookEventType.BEFORE,
        ...     event_name=CortexEvents.METRIC_CREATED,
        ...     params={"name": "Revenue"}
        ... )
    """

    operation: str
    manager: str
    action: str
    event_type: HookEventType
    event_name: CortexEvents
    params: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class MetricsEventContext(EventContext):
    """
    Context for metrics operations.

    Extends EventContext with metrics-specific fields.

    Attributes:
        metric_id: Metric ID
        environment_id: Environment ID
        data_model_id: Data model ID

    Examples:
        >>> context = MetricsEventContext(
        ...     operation="metrics.create",
        ...     manager="metrics",
        ...     action="create",
        ...     event_type=HookEventType.AFTER,
        ...     event_name=CortexEvents.METRIC_CREATED,
        ...     params={},
        ...     metric_id=uuid4(),
        ...     environment_id=uuid4(),
        ...     data_model_id=uuid4()
        ... )
    """

    metric_id: Optional[UUID] = None
    environment_id: Optional[UUID] = None
    data_model_id: Optional[UUID] = None


class DataSourcesEventContext(EventContext):
    """
    Context for data source operations.

    Attributes:
        data_source_id: Data source ID
        environment_id: Environment ID
        file_id: File ID (for file-based sources)
        filename: Filename
        file_size: File size in bytes
        mime_type: MIME type

    Examples:
        >>> context = DataSourcesEventContext(
        ...     operation="data_sources.create",
        ...     manager="data_sources",
        ...     action="create",
        ...     event_type=HookEventType.AFTER,
        ...     event_name=CortexEvents.DATA_SOURCE_CREATED,
        ...     params={},
        ...     data_source_id=uuid4()
        ... )
    """

    data_source_id: Optional[UUID] = None
    environment_id: Optional[UUID] = None
    file_id: Optional[UUID] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class FileStorageEventContext(EventContext):
    """
    Context for file storage operations.

    Attributes:
        file_id: File ID
        filename: Filename
        file_size: File size in bytes
        mime_type: MIME type
        workspace_id: Workspace ID
        environment_id: Environment ID

    Examples:
        >>> context = FileStorageEventContext(
        ...     operation="file_storage.upload",
        ...     manager="file_storage",
        ...     action="upload",
        ...     event_type=HookEventType.AFTER,
        ...     event_name=CortexEvents.FILE_UPLOADED,
        ...     params={},
        ...     file_id=uuid4(),
        ...     filename="data.csv"
        ... )
    """

    file_id: Optional[UUID] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    workspace_id: Optional[UUID] = None
    environment_id: Optional[UUID] = None


class DashboardsEventContext(EventContext):
    """
    Context for dashboard operations.

    Attributes:
        dashboard_id: Dashboard ID
        environment_id: Environment ID
        view_alias: View alias
        widget_alias: Widget alias

    Examples:
        >>> context = DashboardsEventContext(
        ...     operation="dashboards.execute",
        ...     manager="dashboards",
        ...     action="execute",
        ...     event_type=HookEventType.AFTER,
        ...     event_name=CortexEvents.DASHBOARD_EXECUTED,
        ...     params={},
        ...     dashboard_id=uuid4()
        ... )
    """

    dashboard_id: Optional[UUID] = None
    environment_id: Optional[UUID] = None
    view_alias: Optional[str] = None
    widget_alias: Optional[str] = None


class QueryEventContext(EventContext):
    """
    Context for query execution operations.

    Attributes:
        metric_id: Metric ID
        query_sql: SQL query
        duration_ms: Execution duration in milliseconds
        row_count: Number of rows returned
        cache_hit: Whether result was from cache

    Examples:
        >>> context = QueryEventContext(
        ...     operation="metrics.execute",
        ...     manager="metrics",
        ...     action="execute",
        ...     event_type=HookEventType.AFTER,
        ...     event_name=CortexEvents.METRIC_EXECUTED,
        ...     params={},
        ...     metric_id=uuid4(),
        ...     duration_ms=123.45,
        ...     row_count=100,
        ...     cache_hit=False
        ... )
    """

    metric_id: Optional[UUID] = None
    query_sql: Optional[str] = None
    duration_ms: Optional[float] = None
    row_count: Optional[int] = None
    cache_hit: Optional[bool] = None
