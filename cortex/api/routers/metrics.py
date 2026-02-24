from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
    MetricVersionCreateRequest,
    MetricRecommendationsRequest
)
from cortex.sdk.schemas.requests.doctor import MetricDiagnoseRequest
from cortex.core.types.doctor import DiagnosisResult
from cortex.api.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
    MetricVersionResponse,
    MetricVersionListResponse,
    MetricRecommendationsResponse
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError


# Create router instance
MetricsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@MetricsRouter.post("/metrics", response_model=MetricResponse,
                   status_code=status.HTTP_201_CREATED,
                   tags=["Metrics"])
async def create_metric(metric_data: MetricCreateRequest):
    """Create a new metric."""
    try:
        return _client.metrics.create(metric_data)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.post("/metrics/diagnose", response_model=DiagnosisResult, tags=["Metrics"])
async def diagnose_metric(request: MetricDiagnoseRequest):
    """
    Diagnose a metric for configuration issues.

    Accepts either a metric_id (to diagnose a saved metric) or an inline metric
    definition. Runs through compilation, validation, SQL generation, and execution
    stages, collecting all errors and generating fix suggestions where possible.
    """
    try:
        result = _client.metrics.diagnose(request)
        # FastAPI will serialize based on response_model=DiagnosisResult
        # Pydantic's smart Union mode will use actual runtime type
        return result
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.get("/metrics/{metric_id}", response_model=MetricResponse,
                  tags=["Metrics"])
async def get_metric(metric_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Get a specific metric by ID, validating it belongs to the environment."""
    try:
        return _client.metrics.get(metric_id, environment_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.get("/metrics", response_model=MetricListResponse,
                  tags=["Metrics"])
async def list_metrics(
    environment_id: UUID = Query(..., description="Environment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    data_model_id: Optional[UUID] = Query(None, description="Filter by data model ID"),
    public_only: Optional[bool] = Query(None, description="Filter by public status"),
    valid_only: Optional[bool] = Query(None, description="Filter by valid status")
):
    """List metrics for a specific environment with optional filtering and pagination."""
    try:
        return _client.metrics.list(
            environment_id=environment_id,
            page=page,
            page_size=page_size,
            data_model_id=data_model_id,
            public_only=public_only,
            valid_only=valid_only
        )
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.put("/metrics/{metric_id}", response_model=MetricResponse,
                  tags=["Metrics"])
async def update_metric(metric_id: UUID, metric_data: MetricUpdateRequest):
    """Update an existing metric, validating it belongs to the environment."""
    try:
        return _client.metrics.update(metric_id, metric_data)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.delete("/metrics/{metric_id}",
                     status_code=status.HTTP_204_NO_CONTENT,
                     tags=["Metrics"])
async def delete_metric(metric_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Delete a metric, validating it belongs to the environment."""
    try:
        _client.metrics.delete(metric_id, environment_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.post("/metrics/{metric_id}/execute", response_model=MetricExecutionResponse,
                   tags=["Metrics"])
async def execute_metric(metric_id: UUID, execution_request: MetricExecutionRequest):
    """Execute a metric with parameters or preview the generated query."""
    try:
        return _client.metrics.execute(metric_id, execution_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.post("/metrics/{metric_id}/clone", response_model=MetricResponse,
                   tags=["Metrics"])
async def clone_metric(metric_id: UUID, clone_request: MetricCloneRequest):
    """Clone a metric to another data model."""
    try:
        return _client.metrics.clone(metric_id, clone_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.get("/metrics/{metric_id}/versions", response_model=MetricVersionListResponse,
                  tags=["Metrics"])
async def list_metric_versions(metric_id: UUID):
    """List all versions of a metric."""
    try:
        return _client.metrics.list_versions(metric_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.post("/metrics/{metric_id}/versions", response_model=MetricVersionResponse,
                   status_code=status.HTTP_201_CREATED,
                   tags=["Metrics"])
async def create_metric_version(metric_id: UUID, version_request: MetricVersionCreateRequest):
    """Create a new version of a metric."""
    try:
        return _client.metrics.create_version(metric_id, version_request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@MetricsRouter.post("/metrics/recommendations", response_model=MetricRecommendationsResponse,
                   tags=["Metrics"])
async def generate_metric_recommendations(request: MetricRecommendationsRequest):
    """
    Generate metric recommendations from a data source schema.

    This endpoint analyzes the schema of a data source and generates
    a set of recommended metrics based on deterministic rules.
    The generated metrics are not saved - they are returned for review.
    """
    try:
        return _client.metrics.generate_recommendations(request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 