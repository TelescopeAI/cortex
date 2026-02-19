"""
Query history direct handler - Core service calls.

Handles query history operations in Direct mode.
"""
from typing import List
from uuid import UUID

from cortex.core.query.db.service import QueryHistoryCRUD
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
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def get_query_history(request: QueryHistoryFilterRequest) -> QueryLogListResponse:
    """
    Get query history with filtering - direct Core service call.

    Args:
        request: Query history filter request

    Returns:
        Query log list response
    """
    try:
        query_logs = QueryHistoryCRUD.get_recent_query_logs(
            limit=request.limit if request.limit is not None else None,
            metric_id=request.metric_id,
            data_model_id=request.data_model_id,
            success=request.success,
            cache_mode=request.cache_mode,
            executed_after=request.executed_after,
            executed_before=request.executed_before
        )

        # Convert to response format
        entries = []
        for log in query_logs:
            entries.append(QueryLogResponse(
                id=log.id,
                metric_id=log.metric_id,
                data_model_id=log.data_model_id,
                query=log.query,
                parameters=log.parameters,
                context_id=log.context_id,
                meta=log.meta,
                cache_mode=log.cache_mode,
                query_hash=log.query_hash,
                duration=log.duration,
                row_count=log.row_count,
                success=log.success,
                error_message=log.error_message,
                executed_at=log.executed_at
            ))

        return QueryLogListResponse(
            entries=entries,
            total_count=len(entries)
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_query_log(query_id: UUID) -> QueryLogResponse:
    """
    Get a specific query log by ID - direct Core service call.

    Args:
        query_id: Query log ID

    Returns:
        Query log response
    """
    try:
        query_log = QueryHistoryCRUD.get_query_log_by_id(query_id)
        if query_log is None:
            raise CortexNotFoundError(f"Query log with ID {query_id} not found")

        return QueryLogResponse(
            id=query_log.id,
            metric_id=query_log.metric_id,
            data_model_id=query_log.data_model_id,
            query=query_log.query,
            parameters=query_log.parameters,
            context_id=query_log.context_id,
            meta=query_log.meta,
            cache_mode=query_log.cache_mode,
            query_hash=query_log.query_hash,
            duration=query_log.duration,
            row_count=query_log.row_count,
            success=query_log.success,
            error_message=query_log.error_message,
            executed_at=query_log.executed_at
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_execution_stats(request: QueryHistoryStatsRequest) -> ExecutionStatsResponse:
    """
    Get aggregated execution statistics - direct Core service call.

    Args:
        request: Query history stats request

    Returns:
        Execution stats response
    """
    try:
        stats = QueryHistoryCRUD.get_execution_stats(
            metric_id=request.metric_id,
            data_model_id=request.data_model_id,
            time_range=request.time_range
        )

        return ExecutionStatsResponse(
            total_executions=stats["total_executions"],
            successful_executions=stats["successful_executions"],
            failed_executions=stats["failed_executions"],
            success_rate=stats["success_rate"],
            average_duration_ms=stats["average_duration_ms"],
            cache_hit_rate=stats.get("cache_hit_rate", 0.0)
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_slow_queries(request: SlowQueriesRequest) -> List[SlowQueryResponse]:
    """
    Get slowest queries for performance analysis - direct Core service call.

    Args:
        request: Slow queries request

    Returns:
        List of slow query responses
    """
    try:
        slow_queries = QueryHistoryCRUD.get_slow_queries(
            limit=request.limit,
            time_range=request.time_range,
            threshold_ms=request.threshold_ms
        )

        # Convert to response format
        responses = []
        for query in slow_queries:
            responses.append(SlowQueryResponse(
                id=query.id,
                metric_id=query.metric_id,
                data_model_id=query.data_model_id,
                query=query.query,
                duration=query.duration,
                row_count=query.row_count,
                success=query.success,
                executed_at=query.executed_at,
                cache_mode=query.cache_mode
            ))

        return responses
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def clear_query_history(request: ClearQueryHistoryRequest) -> dict:
    """
    Clear query history with optional time-based filtering - direct Core service call.

    Args:
        request: Clear query history request

    Returns:
        Success message with count
    """
    try:
        deleted_count = QueryHistoryCRUD.clear_query_history(older_than=request.older_than)
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        raise CoreExceptionMapper().map(e)
