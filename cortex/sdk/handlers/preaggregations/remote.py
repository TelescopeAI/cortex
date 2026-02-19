"""
Pre-aggregations remote handler - HTTP API calls.

Handles pre-aggregation operations in API mode.
"""
from typing import Optional

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.core.preaggregations.models import PreAggregationSpec
from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest
from cortex.sdk.schemas.responses.preaggregations import (
    PreAggregationUpsertResponse,
    PreAggregationListResponse,
    PreAggregationStatusResponse
)


def upsert_preaggregation_spec(
    client: CortexHTTPClient,
    request: PreAggregationUpsertRequest
) -> PreAggregationUpsertResponse:
    """
    Create or update a pre-aggregation spec - HTTP API call.

    Args:
        client: HTTP client
        request: Pre-aggregation upsert request

    Returns:
        Upsert response
    """
    response = client.post("/pre-aggregations", data=request.model_dump())
    return PreAggregationUpsertResponse(**response)


def list_preaggregation_specs(
    client: CortexHTTPClient,
    metric_id: Optional[str] = None
) -> PreAggregationListResponse:
    """
    List pre-aggregation specs - HTTP API call.

    Args:
        client: HTTP client
        metric_id: Optional metric ID to filter by

    Returns:
        List of pre-aggregation specs
    """
    params = {"metric_id": metric_id} if metric_id else None
    response = client.get("/pre-aggregations", params=params)
    return PreAggregationListResponse(**response)


def get_preaggregation_spec(
    client: CortexHTTPClient,
    spec_id: str
) -> PreAggregationSpec:
    """
    Get a pre-aggregation spec by ID - HTTP API call.

    Args:
        client: HTTP client
        spec_id: Pre-aggregation spec ID

    Returns:
        Pre-aggregation spec
    """
    response = client.get(f"/pre-aggregations/{spec_id}")
    return PreAggregationSpec(**response)


def refresh_preaggregation_spec(
    client: CortexHTTPClient,
    spec_id: str,
    dry_run: bool = False
) -> PreAggregationStatusResponse:
    """
    Build or refresh a pre-aggregation spec - HTTP API call.

    Args:
        client: HTTP client
        spec_id: Pre-aggregation spec ID
        dry_run: If True, only validate without building

    Returns:
        Status response
    """
    params = {"dry_run": dry_run}
    response = client.post(f"/pre-aggregations/{spec_id}/refresh", params=params)
    return PreAggregationStatusResponse(**response)


def get_preaggregation_status(
    client: CortexHTTPClient,
    spec_id: str
) -> PreAggregationStatusResponse:
    """
    Get pre-aggregation spec status - HTTP API call.

    Args:
        client: HTTP client
        spec_id: Pre-aggregation spec ID

    Returns:
        Status response
    """
    response = client.get(f"/pre-aggregations/{spec_id}/status")
    return PreAggregationStatusResponse(**response)


def delete_preaggregation_spec(
    client: CortexHTTPClient,
    spec_id: str
) -> dict:
    """
    Delete a pre-aggregation spec - HTTP API call.

    Args:
        client: HTTP client
        spec_id: Pre-aggregation spec ID

    Returns:
        Success message
    """
    response = client.delete(f"/pre-aggregations/{spec_id}")
    return response
