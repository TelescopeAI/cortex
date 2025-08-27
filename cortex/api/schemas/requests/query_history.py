from typing import Optional
from datetime import datetime
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.query.history.logger import QueryCacheMode


class QueryHistoryFilterRequest(TSModel):
    """Request schema for filtering query history."""
    limit: Optional[int] = None
    metric_id: Optional[UUID] = None
    data_model_id: Optional[UUID] = None
    success: Optional[bool] = None
    cache_mode: Optional[QueryCacheMode] = None
    executed_after: Optional[datetime] = None
    executed_before: Optional[datetime] = None


class QueryHistoryStatsRequest(TSModel):
    """Request schema for query history statistics."""
    metric_id: Optional[UUID] = None
    data_model_id: Optional[UUID] = None
    time_range: Optional[str] = None  # "1h", "24h", "7d", "30d"


class SlowQueriesRequest(TSModel):
    """Request schema for slow queries analysis."""
    limit: Optional[int] = 10
    time_range: Optional[str] = None  # "1h", "24h", "7d", "30d"
    threshold_ms: Optional[float] = 1000.0


class ClearQueryHistoryRequest(TSModel):
    """Request schema for clearing query history."""
    older_than: Optional[datetime] = None
