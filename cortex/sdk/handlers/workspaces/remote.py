"""
Workspaces remote handler - HTTP API calls.

Handles workspace operations in API mode.
"""
from typing import List
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.workspaces import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest
)
from cortex.sdk.schemas.responses.workspaces import WorkspaceResponse


def create_workspace(
    client: CortexHTTPClient,
    request: WorkspaceCreateRequest
) -> WorkspaceResponse:
    """
    Create a new workspace - HTTP API call.

    Args:
        client: HTTP client
        request: Workspace creation request

    Returns:
        Created workspace response
    """
    response = client.post("/workspaces", data=request.model_dump())
    return WorkspaceResponse(**response)


def get_workspace(
    client: CortexHTTPClient,
    workspace_id: UUID
) -> WorkspaceResponse:
    """
    Get a workspace by ID - HTTP API call.

    Args:
        client: HTTP client
        workspace_id: Workspace ID

    Returns:
        Workspace response
    """
    response = client.get(f"/workspaces/{workspace_id}")
    return WorkspaceResponse(**response)


def list_workspaces(client: CortexHTTPClient) -> List[WorkspaceResponse]:
    """
    List all workspaces - HTTP API call.

    Args:
        client: HTTP client

    Returns:
        List of workspace responses
    """
    response = client.get("/workspaces")
    return [WorkspaceResponse(**w) for w in response]


def update_workspace(
    client: CortexHTTPClient,
    workspace_id: UUID,
    request: WorkspaceUpdateRequest
) -> WorkspaceResponse:
    """
    Update a workspace - HTTP API call.

    Args:
        client: HTTP client
        workspace_id: Workspace ID
        request: Update request

    Returns:
        Updated workspace response
    """
    response = client.put(f"/workspaces/{workspace_id}", data=request.model_dump())
    return WorkspaceResponse(**response)


def delete_workspace(
    client: CortexHTTPClient,
    workspace_id: UUID
) -> None:
    """
    Delete a workspace - HTTP API call.

    Args:
        client: HTTP client
        workspace_id: Workspace ID
    """
    client.delete(f"/workspaces/{workspace_id}")
