"""
Query history remote handler - HTTP API calls.

Handles query history operations in API mode.
"""
from typing import List
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
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


def get_query_history(
    client: CortexHTTPClient,
    request: QueryHistoryFilterRequest
) -> QueryLogListResponse:
    """
    Get query history with filtering - HTTP API call.

    Args:
        client: HTTP client
        request: Query history filter request

    Returns:
        Query log list response
    """
    response = client.post("/query/history", data=request.model_dump())
    return QueryLogListResponse(**response)


def get_query_log(
    client: CortexHTTPClient,
    query_id: UUID
) -> QueryLogResponse:
    """
    Get a specific query log by ID - HTTP API call.

    Args:
        client: HTTP client
        query_id: Query log ID

    Returns:
        Query log response
    """
    response = client.get(f"/query/history/{query_id}")
    return QueryLogResponse(**response)


def get_execution_stats(
    client: CortexHTTPClient,
    request: QueryHistoryStatsRequest
) -> ExecutionStatsResponse:
    """
    Get aggregated execution statistics - HTTP API call.

    Args:
        client: HTTP client
        request: Query history stats request

    Returns:
        Execution stats response
    """
    response = client.post("/query/history/stats", data=request.model_dump())
    return ExecutionStatsResponse(**response)


def get_slow_queries(
    client: CortexHTTPClient,
    request: SlowQueriesRequest
) -> List[SlowQueryResponse]:
    """
    Get slowest queries for performance analysis - HTTP API call.

    Args:
        client: HTTP client
        request: Slow queries request

    Returns:
        List of slow query responses
    """
    response = client.post("/query/history/slow-queries", data=request.model_dump())
    return [SlowQueryResponse(**query) for query in response]


def clear_query_history(
    client: CortexHTTPClient,
    request: ClearQueryHistoryRequest
) -> dict:
    """
    Clear query history with optional time-based filtering - HTTP API call.

    Args:
        client: HTTP client
        request: Clear query history request

    Returns:
        Success message with count
    """
    response = client.post("/query/history/clear", data=request.model_dump())
    return response
