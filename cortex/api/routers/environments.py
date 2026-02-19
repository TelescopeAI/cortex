from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.requests.environments import EnvironmentCreateRequest, EnvironmentUpdateRequest
from cortex.api.schemas.responses.environments import EnvironmentResponse
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexSDKError

EnvironmentsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@EnvironmentsRouter.post(
    "/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Environments"]
)
async def create_environment(environment_data: EnvironmentCreateRequest):
    """Create a new environment"""
    try:
        environment_response = _client.environments.create(environment_data)
        return environment_response
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


@EnvironmentsRouter.get(
    "/environments",
    response_model=List[EnvironmentResponse],
    tags=["Environments"]
)
async def list_environments(workspace_id: UUID):
    """List all environments in a workspace"""
    try:
        environments = _client.environments.list(workspace_id)
        return environments
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


@EnvironmentsRouter.get(
    "/environments/{environment_id}",
    response_model=EnvironmentResponse,
    tags=["Environments"]
)
async def get_environment(environment_id: UUID):
    """Get an environment by ID"""
    try:
        environment_response = _client.environments.get(environment_id)
        return environment_response
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


@EnvironmentsRouter.put(
    "/environments/{environment_id}",
    response_model=EnvironmentResponse,
    tags=["Environments"]
)
async def update_environment(environment_id: UUID, environment_data: EnvironmentUpdateRequest):
    """Update an environment"""
    try:
        updated_environment = _client.environments.update(environment_id, environment_data)
        return updated_environment
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


@EnvironmentsRouter.delete(
    "/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Environments"]
)
async def delete_environment(environment_id: UUID):
    """Delete an environment"""
    try:
        _client.environments.delete(environment_id)
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
