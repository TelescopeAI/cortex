from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.core.consumers.consumer import Consumer
from cortex.core.consumers.db.service import ConsumerCRUD
from cortex.core.exceptions.consumers import ConsumerDoesNotExistError, ConsumerAlreadyExistsError
from cortex.api.schemas.requests.consumer.consumers import ConsumerCreateRequest, ConsumerUpdateRequest
from cortex.core.exceptions.environments import EnvironmentDoesNotExistError
from cortex.core.consumers.db.group_service import ConsumerGroupCRUD

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
            organization=consumer_data.organization,
            properties=consumer_data.properties
        )
        created_consumer = ConsumerCRUD.add_consumer(consumer)
        consumer_dict = created_consumer.model_dump()
        consumer_dict["groups"] = []  # New consumer has no groups
        return ConsumerResponse(**consumer_dict)
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
        
        # Get groups for this consumer
        from cortex.core.consumers.db.group_service import ConsumerGroupCRUD
        groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer_id)
        groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]
        
        consumer_dict = consumer.model_dump()
        consumer_dict["groups"] = groups_data
        
        return ConsumerResponse(**consumer_dict)
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
        
        # Get groups for each consumer
        from cortex.core.consumers.db.group_service import ConsumerGroupCRUD
        consumer_responses = []
        
        for consumer in consumers:
            groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer.id)
            groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]
            
            consumer_dict = consumer.model_dump()
            consumer_dict["groups"] = groups_data
            
            consumer_responses.append(ConsumerResponse(**consumer_dict))
        
        return consumer_responses
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
        # Get existing consumer first
        existing_consumer = ConsumerCRUD.get_consumer(consumer_id)
        
        # Update only the fields that are provided
        if consumer_data.first_name is not None:
            existing_consumer.first_name = consumer_data.first_name
        if consumer_data.last_name is not None:
            existing_consumer.last_name = consumer_data.last_name
        if consumer_data.email is not None:
            existing_consumer.email = consumer_data.email
        if consumer_data.organization is not None:
            existing_consumer.organization = consumer_data.organization
        # Allow null values for properties to clear them
        if hasattr(consumer_data, 'properties'):
            existing_consumer.properties = consumer_data.properties
            
        updated_consumer = ConsumerCRUD.update_consumer(existing_consumer)
        
        # Get groups for this consumer
        groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer_id)
        groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]
        
        consumer_dict = updated_consumer.model_dump()
        consumer_dict["groups"] = groups_data
        
        return ConsumerResponse(**consumer_dict)
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