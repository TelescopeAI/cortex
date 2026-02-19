from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Body

from cortex.api.schemas.requests.query_history import (
    QueryHistoryFilterRequest, QueryHistoryStatsRequest, SlowQueriesRequest, ClearQueryHistoryRequest
)
from cortex.api.schemas.responses.query_history import (
    QueryLogResponse, QueryLogListResponse, ExecutionStatsResponse, SlowQueryResponse
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexSDKError

QueryHistoryRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


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
        response = _client.query_history.get_query_history(filter_by)
        return response
    except CortexSDKError as e:
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
        response = _client.query_history.get_query_log(query_id)
        return response
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexSDKError as e:
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
        response = _client.query_history.get_execution_stats(stats_request)
        return response
    except CortexSDKError as e:
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
        responses = _client.query_history.get_slow_queries(slow_queries_request)
        return responses
    except CortexSDKError as e:
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
        result = _client.query_history.clear_query_history(clear_request)
        return result
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear query history: {str(e)}"
        )
