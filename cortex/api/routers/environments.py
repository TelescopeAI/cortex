from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.core.exceptions.environments import NoEnvironmentsExistError, EnvironmentDoesNotExistError
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.core.exceptions.workspaces import WorkspaceDoesNotExistError
from cortex.api.schemas.requests.environments import EnvironmentCreateRequest, EnvironmentUpdateRequest
from cortex.api.schemas.responses.environments import EnvironmentResponse
from cortex.core.workspaces.environments.environment import WorkspaceEnvironment

EnvironmentsRouter = APIRouter()


@EnvironmentsRouter.post(
    "/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Environments"]
)
async def create_environment(environment_data: EnvironmentCreateRequest):
    """Create a new environment"""
    try:
        environment = WorkspaceEnvironment(
            workspace_id=environment_data.workspace_id,
            name=environment_data.name,
            description=environment_data.description
        )
        created_environment = EnvironmentCRUD.add_environment(environment)
        return EnvironmentResponse(**created_environment.model_dump())
    except WorkspaceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
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
        environments = EnvironmentCRUD.get_environments_by_workspace(workspace_id)
        return [EnvironmentResponse(**env.model_dump()) for env in environments]
    except WorkspaceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except NoEnvironmentsExistError:
        return []
    except Exception as e:
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
        environment = EnvironmentCRUD.get_environment(environment_id)
        return EnvironmentResponse(**environment.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
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
        existing_environment = EnvironmentCRUD.get_environment(environment_id)
        
        if environment_data.name is not None:
            existing_environment.name = environment_data.name
        if environment_data.description is not None:
            existing_environment.description = environment_data.description

        updated_environment = EnvironmentCRUD.update_environment(existing_environment)
        return EnvironmentResponse(**updated_environment.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
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
        environment = EnvironmentCRUD.get_environment(environment_id)
        if EnvironmentCRUD.delete_environment(environment):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete environment"
        )
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )