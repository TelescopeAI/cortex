from datetime import datetime
from typing import List
from uuid import UUID

import pytz
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.responses.workspaces import WorkspaceResponse
from cortex.core.exceptions.workspaces import WorkspaceDoesNotExistError, NoWorkspacesExistError, WorkspaceAlreadyExistsError
from cortex.core.workspaces.db.workspace_service import WorkspaceCRUD
from cortex.core.workspaces.workspace import Workspace
from cortex.api.schemas.requests.workspaces import WorkspaceCreateRequest, WorkspaceUpdateRequest

WorkspaceRouter = APIRouter()


@WorkspaceRouter.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Workspaces"]
)
async def create_workspace(workspace_data: WorkspaceCreateRequest):
    """Create a new workspace"""
    try:
        workspace = Workspace(
            name=workspace_data.name,
            description=workspace_data.description
        )
        created_workspace = WorkspaceCRUD.add_workspace(workspace)
        return WorkspaceResponse(**created_workspace.model_dump())
    except WorkspaceAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
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
        workspace = WorkspaceCRUD.get_workspace(workspace_id)
        return WorkspaceResponse(**workspace.model_dump())
    except WorkspaceDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    except Exception as e:
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
        workspaces = WorkspaceCRUD.get_all_workspaces()
        return [WorkspaceResponse(**w.model_dump()) for w in workspaces]
    except NoWorkspacesExistError:
        return []
    except Exception as e:
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
        # First get the existing workspace
        existing_workspace = WorkspaceCRUD.get_workspace(workspace_id)

        # Update only the fields that are provided
        if workspace_data.name is not None:
            existing_workspace.name = workspace_data.name
        if workspace_data.description is not None:
            existing_workspace.description = workspace_data.description
        existing_workspace.updated_at = datetime.now(pytz.UTC)
        updated_workspace = WorkspaceCRUD.update_workspace(existing_workspace)
        return WorkspaceResponse(**updated_workspace.model_dump())
    except WorkspaceDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    except Exception as e:
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
        workspace = WorkspaceCRUD.get_workspace(workspace_id)
        if WorkspaceCRUD.delete_workspace(workspace):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete workspace"
        )
    except WorkspaceDoesNotExistError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace with ID {workspace_id} not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )