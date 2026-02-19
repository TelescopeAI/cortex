from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.data_models import (
    DataModelCreateRequest,
    DataModelUpdateRequest,
    ModelExecutionRequest
)
from cortex.api.schemas.responses.data_models import (
    DataModelResponse,
    DataModelListResponse,
    ModelExecutionResponse
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError

# Create router instance
DataModelsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@DataModelsRouter.post("/data/models", response_model=DataModelResponse,
                       status_code=status.HTTP_201_CREATED,
                       tags=["Data Models"]
)
async def create_data_model(model_data: DataModelCreateRequest):
    """Create a new data model with semantic definitions."""
    try:
        return _client.data_models.create(model_data)
    except CortexValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataModelsRouter.get("/data/models/{model_id}", response_model=DataModelResponse,
                      tags=["Data Models"]
)
async def get_data_model(model_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Get a specific data model by ID, validating it belongs to the environment."""
    try:
        return _client.data_models.get(model_id, environment_id)
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataModelsRouter.get("/data/models", response_model=DataModelListResponse,
                      tags=["Data Models"]
)
async def list_data_models(
    environment_id: UUID = Query(..., description="Environment ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """List data models for a specific environment with optional filtering and pagination."""
    try:
        return _client.data_models.list(environment_id, page, page_size, is_active)
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataModelsRouter.put("/data/models/{model_id}", response_model=DataModelResponse,
                      tags=["Data Models"]
)
async def update_data_model(model_id: UUID, model_data: DataModelUpdateRequest):
    """Update an existing data model, validating it belongs to the environment."""
    try:
        return _client.data_models.update(model_id, model_data)
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataModelsRouter.delete("/data/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT,
                         tags=["Data Models"]
)
async def delete_data_model(model_id: UUID, environment_id: UUID = Query(..., description="Environment ID")):
    """Delete a data model (soft delete), validating it belongs to the environment."""
    try:
        _client.data_models.delete(model_id, environment_id)
        return None
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataModelsRouter.post("/data/models/{model_id}/execute", response_model=ModelExecutionResponse,
                       tags=["Data Models"]
)
async def execute_data_model(model_id: UUID, execution_request: ModelExecutionRequest):
    """Execute a data model query."""
    try:
        return _client.data_models.execute(model_id, execution_request)
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 