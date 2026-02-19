"""
Remote mode implementations for metrics operations.

Makes HTTP API calls to remote Cortex server.
"""
from typing import Optional
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
)
from cortex.sdk.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
)


def list_metrics(
    client: CortexHTTPClient,
    environment_id: UUID,
    page: int = 1,
    page_size: int = 20,
    data_model_id: Optional[UUID] = None,
    public_only: Optional[bool] = None,
    valid_only: Optional[bool] = None
) -> MetricListResponse:
    """
    List metrics - HTTP API call.

    Args:
        client: HTTP client instance
        environment_id: Environment ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        data_model_id: Optional filter by data model ID
        public_only: Optional filter by public status
        valid_only: Optional filter by valid status

    Returns:
        MetricListResponse
    """
    params = {
        "environment_id": str(environment_id),
        "page": page,
        "page_size": page_size,
    }
    if data_model_id is not None:
        params["data_model_id"] = str(data_model_id)
    if public_only is not None:
        params["public_only"] = public_only
    if valid_only is not None:
        params["valid_only"] = valid_only

    response = client.get("/metrics", params=params)
    return MetricListResponse(**response)


def get_metric(
    client: CortexHTTPClient, metric_id: UUID, environment_id: Optional[UUID] = None
) -> MetricResponse:
    """
    Get metric by ID - HTTP API call.

    Args:
        client: HTTP client instance
        metric_id: Metric ID
        environment_id: Optional environment ID

    Returns:
        MetricResponse
    """
    params = {"environment_id": str(environment_id)} if environment_id else None
    response = client.get(f"/metrics/{metric_id}", params=params)
    return MetricResponse(**response)


def create_metric(client: CortexHTTPClient, request: MetricCreateRequest) -> MetricResponse:
    """
    Create metric - HTTP API call.

    Args:
        client: HTTP client instance
        request: Metric creation request

    Returns:
        MetricResponse
    """
    response = client.post("/metrics", data=request.model_dump())
    return MetricResponse(**response)


def update_metric(
    client: CortexHTTPClient, metric_id: UUID, request: MetricUpdateRequest
) -> MetricResponse:
    """
    Update metric - HTTP API call.

    Args:
        client: HTTP client instance
        metric_id: Metric ID
        request: Metric update request

    Returns:
        MetricResponse
    """
    response = client.put(f"/metrics/{metric_id}", data=request.model_dump(exclude_unset=True))
    return MetricResponse(**response)


def delete_metric(
    client: CortexHTTPClient, metric_id: UUID, environment_id: Optional[UUID] = None
) -> None:
    """
    Delete metric - HTTP API call.

    Args:
        client: HTTP client instance
        metric_id: Metric ID
        environment_id: Optional environment ID
    """
    params = {"environment_id": str(environment_id)} if environment_id else None
    client.delete(f"/metrics/{metric_id}", params=params)


def execute_metric(
    client: CortexHTTPClient, metric_id: UUID, request: MetricExecutionRequest
) -> MetricExecutionResponse:
    """
    Execute metric - HTTP API call.

    Args:
        client: HTTP client instance
        metric_id: Metric ID
        request: Execution request

    Returns:
        MetricExecutionResponse
    """
    response = client.post(f"/metrics/{metric_id}/execute", data=request.model_dump())
    return MetricExecutionResponse(**response)


def clone_metric(
    client: CortexHTTPClient, metric_id: UUID, request: MetricCloneRequest
) -> MetricResponse:
    """
    Clone metric - HTTP API call.

    Args:
        client: HTTP client instance
        metric_id: Source metric ID
        request: Clone request

    Returns:
        MetricResponse
    """
    response = client.post(f"/metrics/{metric_id}/clone", data=request.model_dump())
    return MetricResponse(**response)
