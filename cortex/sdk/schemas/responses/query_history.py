from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.query.history.logger import QueryCacheMode


class QueryLogResponse(TSModel):
    """Response schema for individual query log entries."""
    id: UUID
    metric_id: UUID
    data_model_id: UUID
    query: str
    parameters: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    cache_mode: Optional[QueryCacheMode] = None
    query_hash: Optional[str] = None
    duration: float  # milliseconds
    row_count: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    executed_at: datetime


class QueryLogListResponse(TSModel):
    """Response schema for listing query log entries."""
    entries: List[QueryLogResponse]
    total_count: int


class ExecutionStatsResponse(TSModel):
    """Response schema for execution statistics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_duration_ms: float
    cache_hit_rate: float


class SlowQueryResponse(TSModel):
    """Response schema for slow query analysis."""
    id: UUID
    metric_id: UUID
    data_model_id: UUID
    query: str
    duration: float  # milliseconds
    row_count: Optional[int] = None
    success: bool
    executed_at: datetime
    cache_mode: Optional[QueryCacheMode] = None
