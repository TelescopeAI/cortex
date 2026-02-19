"""
Data models remote handler - HTTP API calls.

Handles data model operations in API mode.
"""
from typing import Optional
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.data_models import (
    DataModelCreateRequest,
    DataModelUpdateRequest,
    ModelExecutionRequest
)
from cortex.sdk.schemas.responses.data_models import (
    DataModelResponse,
    DataModelListResponse,
    ModelExecutionResponse
)


def create_data_model(
    client: CortexHTTPClient,
    request: DataModelCreateRequest
) -> DataModelResponse:
    """
    Create a new data model - HTTP API call.

    Args:
        client: HTTP client
        request: Data model creation request

    Returns:
        Created data model response
    """
    response = client.post("/data/models", data=request.model_dump())
    return DataModelResponse(**response)


def get_data_model(
    client: CortexHTTPClient,
    model_id: UUID,
    environment_id: UUID
) -> DataModelResponse:
    """
    Get a data model by ID - HTTP API call.

    Args:
        client: HTTP client
        model_id: Data model ID
        environment_id: Environment ID

    Returns:
        Data model response
    """
    params = {"environment_id": str(environment_id)}
    response = client.get(f"/data/models/{model_id}", params=params)
    return DataModelResponse(**response)


def list_data_models(
    client: CortexHTTPClient,
    environment_id: UUID,
    page: int = 1,
    page_size: int = 20,
    is_active: Optional[bool] = None
) -> DataModelListResponse:
    """
    List data models - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID
        page: Page number
        page_size: Page size
        is_active: Optional active status filter

    Returns:
        List of data model responses
    """
    params = {
        "environment_id": str(environment_id),
        "page": page,
        "page_size": page_size
    }
    if is_active is not None:
        params["is_active"] = is_active

    response = client.get("/data/models", params=params)
    return DataModelListResponse(**response)


def update_data_model(
    client: CortexHTTPClient,
    model_id: UUID,
    request: DataModelUpdateRequest
) -> DataModelResponse:
    """
    Update a data model - HTTP API call.

    Args:
        client: HTTP client
        model_id: Data model ID
        request: Update request

    Returns:
        Updated data model response
    """
    response = client.put(f"/data/models/{model_id}", data=request.model_dump())
    return DataModelResponse(**response)


def delete_data_model(
    client: CortexHTTPClient,
    model_id: UUID,
    environment_id: UUID
) -> None:
    """
    Delete a data model (soft delete) - HTTP API call.

    Args:
        client: HTTP client
        model_id: Data model ID
        environment_id: Environment ID
    """
    params = {"environment_id": str(environment_id)}
    client.delete(f"/data/models/{model_id}", params=params)


def execute_data_model(
    client: CortexHTTPClient,
    model_id: UUID,
    request: ModelExecutionRequest
) -> ModelExecutionResponse:
    """
    Execute a data model query - HTTP API call.

    Args:
        client: HTTP client
        model_id: Data model ID
        request: Execution request

    Returns:
        Execution response with results
    """
    response = client.post(
        f"/data/models/{model_id}/execute",
        data=request.model_dump()
    )
    return ModelExecutionResponse(**response)
