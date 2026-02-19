from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.responses.workspaces import WorkspaceResponse
from cortex.api.schemas.requests.workspaces import WorkspaceCreateRequest, WorkspaceUpdateRequest
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError

WorkspaceRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@WorkspaceRouter.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Workspaces"]
)
async def create_workspace(workspace_data: WorkspaceCreateRequest):
    """Create a new workspace"""
    try:
        workspace_response = _client.workspaces.create(workspace_data)
        return workspace_response
    except CortexValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@WorkspaceRouter.get(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    tags=["Workspaces"]
)
async def get_workspace(workspace_id: UUID):
    """Get a workspace by ID"""
    try:
        workspace_response = _client.workspaces.get(workspace_id)
        return workspace_response
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


@WorkspaceRouter.get(
    "/workspaces",
    response_model=List[WorkspaceResponse],
    tags=["Workspaces"]
)
async def list_workspaces():
    """Get all workspaces"""
    try:
        workspaces = _client.workspaces.list()
        return workspaces
    except CortexSDKError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@WorkspaceRouter.put(
    "/workspaces/{workspace_id}",
    response_model=WorkspaceResponse,
    tags=["Workspaces"]
)
async def update_workspace(workspace_id: UUID, workspace_data: WorkspaceUpdateRequest):
    """Update a workspace"""
    try:
        updated_workspace = _client.workspaces.update(workspace_id, workspace_data)
        return updated_workspace
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


@WorkspaceRouter.delete(
    "/workspaces/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Workspaces"]
)
async def delete_workspace(workspace_id: UUID):
    """Delete a workspace"""
    try:
        _client.workspaces.delete(workspace_id)
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
