from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.core.consumers.consumer import Consumer
from cortex.core.consumers.db.service import ConsumerCRUD
from cortex.core.exceptions.consumers import ConsumerDoesNotExistError, ConsumerAlreadyExistsError
from cortex.api.schemas.requests.consumer.consumers import ConsumerCreateRequest, ConsumerUpdateRequest
from cortex.core.exceptions.environments import EnvironmentDoesNotExistError

ConsumersRouter = APIRouter()


@ConsumersRouter.post(
    "/consumers",
    response_model=ConsumerResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Consumers"]
)
async def create_consumer(consumer_data: ConsumerCreateRequest):
    """Create a new consumer"""
    try:
        consumer = Consumer(
            environment_id=consumer_data.environment_id,
            first_name=consumer_data.first_name,
            last_name=consumer_data.last_name,
            email=consumer_data.email,
            organization=consumer_data.organization
        )
        created_consumer = ConsumerCRUD.add_consumer(consumer)
        return ConsumerResponse(**created_consumer.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConsumerAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumersRouter.get(
    "/consumers/{consumer_id}",
    response_model=ConsumerResponse,
    tags=["Consumers"]
)
async def get_consumer(consumer_id: UUID):
    """Get a consumer by ID"""
    try:
        consumer = ConsumerCRUD.get_consumer(consumer_id)
        return ConsumerResponse(**consumer.model_dump())
    except ConsumerDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumersRouter.get(
    "/environments/{environment_id}/consumers",
    response_model=List[ConsumerResponse],
    tags=["Environments"]
)
async def list_consumers(environment_id: UUID):
    """List all consumers in an environment"""
    try:
        consumers = ConsumerCRUD.get_consumers_by_environment(environment_id)
        return [ConsumerResponse(**c.model_dump()) for c in consumers]
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


@ConsumersRouter.put(
    "/consumers/{consumer_id}",
    response_model=ConsumerResponse,
    tags=["Consumers"]
)
async def update_consumer(consumer_id: UUID, consumer_data: ConsumerUpdateRequest):
    """Update a consumer"""
    try:
        updated_consumer = ConsumerCRUD.update_consumer(
            consumer_id=consumer_id,
            first_name=consumer_data.first_name,
            last_name=consumer_data.last_name,
            email=consumer_data.email,
            organization=consumer_data.organization
        )
        return ConsumerResponse(**updated_consumer.model_dump())
    except ConsumerDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumersRouter.delete(
    "/consumers/{consumer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Consumers"]
)
async def delete_consumer(consumer_id: UUID):
    """Delete a consumer"""
    try:
        if ConsumerCRUD.delete_consumer(consumer_id):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete consumer"
        )
    except ConsumerDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )