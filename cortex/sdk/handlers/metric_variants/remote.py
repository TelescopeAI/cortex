"""
Metric variants remote handler - HTTP API calls.

Handles metric variant operations in API mode.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.variants import (
    MetricVariantCreateRequest,
    MetricVariantUpdateRequest,
    MetricVariantExecutionRequest
)
from cortex.sdk.schemas.responses.variants import (
    MetricVariantResponse,
    MetricVariantListResponse,
    MetricVariantExecutionResponse
)


def create_variant(
    client: CortexHTTPClient,
    request: MetricVariantCreateRequest
) -> MetricVariantResponse:
    """
    Create a new metric variant - HTTP API call.

    Args:
        client: HTTP client
        request: Metric variant creation request

    Returns:
        Created metric variant response
    """
    response = client.post("/metrics/variants", data=request.model_dump())
    return MetricVariantResponse(**response)


def list_variants(
    client: CortexHTTPClient,
    environment_id: UUID,
    data_model_id: Optional[UUID] = None,
    source_metric_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> MetricVariantListResponse:
    """
    List metric variants - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID
        data_model_id: Optional data model ID filter
        source_metric_id: Optional source metric ID filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of metric variant responses
    """
    params = {
        "environment_id": str(environment_id),
        "limit": limit,
        "offset": offset
    }
    if data_model_id:
        params["data_model_id"] = str(data_model_id)
    if source_metric_id:
        params["source_metric_id"] = str(source_metric_id)

    response = client.get("/metrics/variants", params=params)
    return MetricVariantListResponse(**response)


def get_variant(
    client: CortexHTTPClient,
    variant_id: UUID,
    environment_id: UUID
) -> MetricVariantResponse:
    """
    Get a metric variant by ID - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID
        environment_id: Environment ID

    Returns:
        Metric variant response
    """
    params = {"environment_id": str(environment_id)}
    response = client.get(f"/metrics/variants/{variant_id}", params=params)
    return MetricVariantResponse(**response)


def update_variant(
    client: CortexHTTPClient,
    variant_id: UUID,
    request: MetricVariantUpdateRequest
) -> MetricVariantResponse:
    """
    Update a metric variant - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID
        request: Update request

    Returns:
        Updated metric variant response
    """
    response = client.put(f"/metrics/variants/{variant_id}", data=request.model_dump())
    return MetricVariantResponse(**response)


def delete_variant(
    client: CortexHTTPClient,
    variant_id: UUID,
    environment_id: UUID
) -> None:
    """
    Delete a metric variant - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID
        environment_id: Environment ID
    """
    params = {"environment_id": str(environment_id)}
    client.delete(f"/metrics/variants/{variant_id}", params=params)


def reset_variant(client: CortexHTTPClient, variant_id: UUID) -> Dict[str, Any]:
    """
    Reset a variant by removing all overrides - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID

    Returns:
        Reset result dictionary
    """
    response = client.post(f"/metrics/variants/{variant_id}/reset")
    return response


def detach_variant(client: CortexHTTPClient, variant_id: UUID) -> Dict[str, Any]:
    """
    Detach a variant by creating a new standalone metric - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID

    Returns:
        Detach result dictionary with new metric ID
    """
    response = client.post(f"/metrics/variants/{variant_id}/detach")
    return response


def execute_variant(
    client: CortexHTTPClient,
    variant_id: UUID,
    request: MetricVariantExecutionRequest
) -> MetricVariantExecutionResponse:
    """
    Execute a metric variant - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID
        request: Execution request

    Returns:
        Execution response with results
    """
    response = client.post(
        f"/metrics/variants/{variant_id}/execute",
        data=request.model_dump()
    )
    return MetricVariantExecutionResponse(**response)


def override_source(client: CortexHTTPClient, variant_id: UUID) -> Dict[str, Any]:
    """
    Override the source metric with the resolved state of this variant - HTTP API call.

    Args:
        client: HTTP client
        variant_id: Variant ID

    Returns:
        Override result dictionary
    """
    response = client.post(f"/metrics/variants/{variant_id}/override-source")
    return response
