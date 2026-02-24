"""
API router for metric variants.

This module provides REST endpoints for creating, reading, updating, and deleting
metric variants, as well as lifecycle operations (reset, detach, override-source).
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.variants import (
    MetricVariantCreateRequest,
    MetricVariantUpdateRequest,
    MetricVariantExecutionRequest,
    MetricVariantCloneRequest
)
from cortex.sdk.schemas.requests.doctor import VariantDiagnoseRequest
from cortex.core.types.doctor import DiagnosisResult
from cortex.api.schemas.responses.variants import (
    MetricVariantResponse,
    MetricVariantListResponse,
    MetricVariantExecutionResponse
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError


# Create router instance
VariantsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@VariantsRouter.post(
    "/metrics/variants",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Metric Variants"],
)
async def create_variant(variant_request: MetricVariantCreateRequest):
    """
    Create a new metric variant.

    Variants inherit from a source metric and can modify it through overrides,
    inclusions, exclusions, derivations, and multi-source composition.
    """
    try:
        return _client.metric_variants.create(variant_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.get(
    "/metrics/variants",
    response_model=MetricVariantListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def list_variants(
    environment_id: UUID = Query(..., description="Environment ID"),
    data_model_id: Optional[UUID] = Query(None, description="Filter by data model ID"),
    source_metric_id: Optional[UUID] = Query(None, description="Filter by source metric ID"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
):
    """
    List metric variants with optional filtering.

    Can filter by source_metric_id to get all variants of a specific metric.
    """
    try:
        return _client.metric_variants.list(
            environment_id=environment_id,
            data_model_id=data_model_id,
            source_metric_id=source_metric_id,
            limit=limit,
            offset=offset
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Execute route placed before /{variant_id} routes to avoid path conflicts
@VariantsRouter.post(
    "/metrics/variants/execute",
    response_model=MetricVariantExecutionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants", "Execution"],
)
async def execute_variant(execution_request: MetricVariantExecutionRequest):
    """
    Execute a metric variant and return results.

    Supports two modes:
    - By ID: provide variant_id in the request body to execute a saved variant
    - Inline: provide a variant definition in the request body to preview without saving
    """
    try:
        return _client.metric_variants.execute(execution_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.post(
    "/metrics/variants/diagnose",
    response_model=DiagnosisResult,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def diagnose_variant(request: VariantDiagnoseRequest):
    """
    Diagnose a metric variant for configuration issues.

    Accepts either a variant_id (to diagnose a saved variant) or an inline variant
    definition. Compiles the variant, then runs the resolved metric through validation,
    SQL generation, and execution stages. Returns all errors and fix suggestions.
    """
    try:
        result = _client.metric_variants.diagnose(request)
        # FastAPI will serialize based on response_model=DiagnosisResult
        # Pydantic's smart Union mode will use actual runtime type
        return result
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.get(
    "/metrics/variants/{variant_id}",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def get_variant(
    variant_id: UUID,
    environment_id: UUID = Query(..., description="Environment ID")
):
    """
    Get a metric variant by ID.

    Returns the variant definition (not the resolved metric).
    """
    try:
        return _client.metric_variants.get(variant_id, environment_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.put(
    "/metrics/variants/{variant_id}",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def update_variant(variant_id: UUID, variant_request: MetricVariantUpdateRequest):
    """
    Update a metric variant.

    Can modify overrides, inclusions, derivations, and combine settings.
    """
    try:
        return _client.metric_variants.update(variant_id, variant_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.delete(
    "/metrics/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Metric Variants"],
)
async def delete_variant(
    variant_id: UUID,
    environment_id: UUID = Query(..., description="Environment ID")
):
    """
    Delete a metric variant.

    This does not affect the source metric. All variant versions are also deleted (CASCADE).
    """
    try:
        _client.metric_variants.delete(variant_id, environment_id)
        return None  # 204 No Content
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/reset",
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def reset_variant(variant_id: UUID):
    """
    Reset a variant by removing all overrides.

    The variant will then exactly match its source metric.
    """
    try:
        return _client.metric_variants.reset(variant_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/detach",
    status_code=status.HTTP_201_CREATED,
    tags=["Metric Variants"],
)
async def detach_variant(variant_id: UUID):
    """
    Detach a variant by creating a new standalone metric from the resolved state.

    Returns the new metric ID.
    """
    try:
        return _client.metric_variants.detach(variant_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/override-source",
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def override_source(variant_id: UUID):
    """
    Override the source metric with the resolved state of this variant.

    WARNING: This modifies the source metric and cannot be undone!
    """
    try:
        return _client.metric_variants.override_source(variant_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
