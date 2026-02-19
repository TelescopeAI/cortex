"""
Workspaces direct handler - Core service calls.

Handles workspace operations in Direct mode.
"""
from typing import List
from uuid import UUID
from datetime import datetime
import pytz

from cortex.core.workspaces.workspace import Workspace
from cortex.core.workspaces.db.workspace_service import WorkspaceCRUD
from cortex.sdk.schemas.requests.workspaces import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest
)
from cortex.sdk.schemas.responses.workspaces import WorkspaceResponse
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_workspace(request: WorkspaceCreateRequest) -> WorkspaceResponse:
    """
    Create a new workspace - direct Core service call.

    Args:
        request: Workspace creation request

    Returns:
        Created workspace response
    """
    try:
        workspace = Workspace(
            name=request.name,
            description=request.description
        )
        created_workspace = WorkspaceCRUD.add_workspace(workspace)
        return WorkspaceResponse(**created_workspace.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_workspace(workspace_id: UUID) -> WorkspaceResponse:
    """
    Get a workspace by ID - direct Core service call.

    Args:
        workspace_id: Workspace ID

    Returns:
        Workspace response
    """
    try:
        workspace = WorkspaceCRUD.get_workspace(workspace_id)
        return WorkspaceResponse(**workspace.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_workspaces() -> List[WorkspaceResponse]:
    """
    List all workspaces - direct Core service call.

    Returns:
        List of workspace responses
    """
    try:
        from cortex.core.exceptions.workspaces import NoWorkspacesExistError

        try:
            workspaces = WorkspaceCRUD.get_all_workspaces()
            return [WorkspaceResponse(**w.model_dump()) for w in workspaces]
        except NoWorkspacesExistError:
            return []
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_workspace(
    workspace_id: UUID,
    request: WorkspaceUpdateRequest
) -> WorkspaceResponse:
    """
    Update a workspace - direct Core service call.

    Args:
        workspace_id: Workspace ID
        request: Update request

    Returns:
        Updated workspace response
    """
    try:
        # First get the existing workspace
        existing_workspace = WorkspaceCRUD.get_workspace(workspace_id)

        # Update only the fields that are provided
        if request.name is not None:
            existing_workspace.name = request.name
        if request.description is not None:
            existing_workspace.description = request.description
        existing_workspace.updated_at = datetime.now(pytz.UTC)

        updated_workspace = WorkspaceCRUD.update_workspace(existing_workspace)
        return WorkspaceResponse(**updated_workspace.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_workspace(workspace_id: UUID) -> None:
    """
    Delete a workspace - direct Core service call.

    Args:
        workspace_id: Workspace ID
    """
    try:
        workspace = WorkspaceCRUD.get_workspace(workspace_id)
        success = WorkspaceCRUD.delete_workspace(workspace)
        if not success:
            raise CortexNotFoundError(f"Workspace with ID {workspace_id} not found")
    except Exception as e:
        raise CoreExceptionMapper().map(e)
