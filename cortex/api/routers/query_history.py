from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query, Body

from cortex.core.query.db.service import QueryHistoryCRUD
from cortex.api.schemas.requests.query_history import (
    QueryHistoryFilterRequest, QueryHistoryStatsRequest, SlowQueriesRequest, ClearQueryHistoryRequest
)
from cortex.api.schemas.responses.query_history import (
    QueryLogResponse, QueryLogListResponse, ExecutionStatsResponse, SlowQueryResponse
)

QueryHistoryRouter = APIRouter()


@QueryHistoryRouter.post(
    "/query/history",
    response_model=QueryLogListResponse,
    tags=["Query History"]
)
async def get_query_history(
    filter_by: QueryHistoryFilterRequest = Body(...)
):
    """Get recent query history with optional filtering."""
    try:
        query_logs = QueryHistoryCRUD.get_recent_query_logs(
            limit=filter_by.limit if filter_by.limit is not None else None,
            metric_id=filter_by.metric_id,
            data_model_id=filter_by.data_model_id,
            success=filter_by.success,
            cache_mode=filter_by.cache_mode,
            executed_after=filter_by.executed_after,
            executed_before=filter_by.executed_before
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query history: {str(e)}"
        )


@QueryHistoryRouter.get(
    "/query/history/{query_id}",
    response_model=QueryLogResponse,
    tags=["Query History"]
)
async def get_query_log(query_id: UUID):
    """Get a specific query log entry by ID."""
    try:
        query_log = QueryHistoryCRUD.get_query_log_by_id(query_id)
        if query_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query log with ID {query_id} not found"
            )
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve query log: {str(e)}"
        )


@QueryHistoryRouter.post(
    "/query/history/stats",
    response_model=ExecutionStatsResponse,
    tags=["Query History"]
)
async def get_execution_stats(
    stats_request: QueryHistoryStatsRequest = Body(...)
):
    """Get aggregated execution statistics."""
    try:
        stats = QueryHistoryCRUD.get_execution_stats(
            metric_id=stats_request.metric_id,
            data_model_id=stats_request.data_model_id,
            time_range=stats_request.time_range
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve execution stats: {str(e)}"
        )


@QueryHistoryRouter.post(
    "/query/history/slow-queries",
    response_model=List[SlowQueryResponse],
    tags=["Query History"]
)
async def get_slow_queries(
    slow_queries_request: SlowQueriesRequest = Body(...)
):
    """Get slowest queries for performance analysis."""
    try:
        slow_queries = QueryHistoryCRUD.get_slow_queries(
            limit=slow_queries_request.limit,
            time_range=slow_queries_request.time_range,
            threshold_ms=slow_queries_request.threshold_ms
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve slow queries: {str(e)}"
        )


@QueryHistoryRouter.post(
    "/query/history/clear",
    status_code=status.HTTP_200_OK,
    tags=["Query History"]
)
async def clear_query_history(
    clear_request: ClearQueryHistoryRequest = Body(...)
):
    """Clear query history with optional time-based filtering (admin only)."""
    try:
        deleted_count = QueryHistoryCRUD.clear_query_history(older_than=clear_request.older_than)
        
        # Return success response with count
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear query history: {str(e)}"
        )



