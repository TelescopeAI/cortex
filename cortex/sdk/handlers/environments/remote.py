"""
Environments remote handler - HTTP API calls.

Handles environment operations in API mode.
"""
from typing import List
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.environments import (
    EnvironmentCreateRequest,
    EnvironmentUpdateRequest
)
from cortex.sdk.schemas.responses.environments import EnvironmentResponse


def create_environment(
    client: CortexHTTPClient,
    request: EnvironmentCreateRequest
) -> EnvironmentResponse:
    """
    Create a new environment - HTTP API call.

    Args:
        client: HTTP client
        request: Environment creation request

    Returns:
        Created environment response
    """
    response = client.post("/environments", data=request.model_dump())
    return EnvironmentResponse(**response)


def get_environment(
    client: CortexHTTPClient,
    environment_id: UUID
) -> EnvironmentResponse:
    """
    Get an environment by ID - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID

    Returns:
        Environment response
    """
    response = client.get(f"/environments/{environment_id}")
    return EnvironmentResponse(**response)


def list_environments(
    client: CortexHTTPClient,
    workspace_id: UUID
) -> List[EnvironmentResponse]:
    """
    List environments in a workspace - HTTP API call.

    Args:
        client: HTTP client
        workspace_id: Workspace ID

    Returns:
        List of environment responses
    """
    params = {"workspace_id": str(workspace_id)}
    response = client.get("/environments", params=params)
    return [EnvironmentResponse(**env) for env in response]


def update_environment(
    client: CortexHTTPClient,
    environment_id: UUID,
    request: EnvironmentUpdateRequest
) -> EnvironmentResponse:
    """
    Update an environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID
        request: Update request

    Returns:
        Updated environment response
    """
    response = client.put(f"/environments/{environment_id}", data=request.model_dump())
    return EnvironmentResponse(**response)


def delete_environment(
    client: CortexHTTPClient,
    environment_id: UUID
) -> None:
    """
    Delete an environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID
    """
    client.delete(f"/environments/{environment_id}")
