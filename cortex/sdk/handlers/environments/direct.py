"""
Environments direct handler - Core service calls.

Handles environment operations in Direct mode.
"""
from typing import List
from uuid import UUID

from cortex.core.workspaces.environments.environment import WorkspaceEnvironment
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.sdk.schemas.requests.environments import (
    EnvironmentCreateRequest,
    EnvironmentUpdateRequest
)
from cortex.sdk.schemas.responses.environments import EnvironmentResponse
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_environment(request: EnvironmentCreateRequest) -> EnvironmentResponse:
    """
    Create a new environment - direct Core service call.

    Args:
        request: Environment creation request

    Returns:
        Created environment response
    """
    try:
        environment = WorkspaceEnvironment(
            workspace_id=request.workspace_id,
            name=request.name,
            description=request.description
        )
        created_environment = EnvironmentCRUD.add_environment(environment)
        return EnvironmentResponse(**created_environment.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_environment(environment_id: UUID) -> EnvironmentResponse:
    """
    Get an environment by ID - direct Core service call.

    Args:
        environment_id: Environment ID

    Returns:
        Environment response
    """
    try:
        environment = EnvironmentCRUD.get_environment(environment_id)
        return EnvironmentResponse(**environment.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_environments(workspace_id: UUID) -> List[EnvironmentResponse]:
    """
    List environments in a workspace - direct Core service call.

    Args:
        workspace_id: Workspace ID

    Returns:
        List of environment responses
    """
    try:
        from cortex.core.exceptions.environments import NoEnvironmentsExistError

        try:
            environments = EnvironmentCRUD.get_environments_by_workspace(workspace_id)
            return [EnvironmentResponse(**env.model_dump()) for env in environments]
        except NoEnvironmentsExistError:
            return []
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_environment(
    environment_id: UUID,
    request: EnvironmentUpdateRequest
) -> EnvironmentResponse:
    """
    Update an environment - direct Core service call.

    Args:
        environment_id: Environment ID
        request: Update request

    Returns:
        Updated environment response
    """
    try:
        existing_environment = EnvironmentCRUD.get_environment(environment_id)

        if request.name is not None:
            existing_environment.name = request.name
        if request.description is not None:
            existing_environment.description = request.description

        updated_environment = EnvironmentCRUD.update_environment(existing_environment)
        return EnvironmentResponse(**updated_environment.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_environment(environment_id: UUID) -> None:
    """
    Delete an environment - direct Core service call.

    Args:
        environment_id: Environment ID
    """
    try:
        environment = EnvironmentCRUD.get_environment(environment_id)
        success = EnvironmentCRUD.delete_environment(environment)
        if not success:
            raise CortexNotFoundError(f"Environment with ID {environment_id} not found")
    except Exception as e:
        raise CoreExceptionMapper().map(e)
