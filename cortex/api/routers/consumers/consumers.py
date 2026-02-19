"""Consumer management router - refactored to use Cortex SDK"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.api.schemas.requests.consumer.consumers import ConsumerCreateRequest, ConsumerUpdateRequest

# Use Cortex SDK client instead of direct Core service calls
from cortex.sdk import CortexClient, CortexNotFoundError, CortexValidationError, CortexSDKError

ConsumersRouter = APIRouter()

# Initialize SDK client in Direct mode (local Core access)
_client = CortexClient(mode="direct")


@ConsumersRouter.post(
    "/consumers",
    response_model=ConsumerResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Consumers"]
)
async def create_consumer(consumer_data: ConsumerCreateRequest):
    """Create a new consumer"""
    try:
        # Use SDK client - handles Consumer model creation and group initialization
        consumer_response = _client.consumers.create(consumer_data)
        return consumer_response
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
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


@ConsumersRouter.get(
    "/consumers/{consumer_id}",
    response_model=ConsumerResponse,
    tags=["Consumers"]
)
async def get_consumer(consumer_id: UUID):
    """Get a consumer by ID"""
    try:
        # Use SDK client - automatically fetches consumer with groups
        consumer_response = _client.consumers.get(consumer_id)
        return consumer_response
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


@ConsumersRouter.get(
    "/environments/{environment_id}/consumers",
    response_model=List[ConsumerResponse],
    tags=["Environments"]
)
async def list_consumers(environment_id: UUID):
    """List all consumers in an environment"""
    try:
        # Use SDK client - automatically fetches consumers with groups
        consumer_responses = _client.consumers.list(environment_id)
        return consumer_responses
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


@ConsumersRouter.put(
    "/consumers/{consumer_id}",
    response_model=ConsumerResponse,
    tags=["Consumers"]
)
async def update_consumer(consumer_id: UUID, consumer_data: ConsumerUpdateRequest):
    """Update a consumer"""
    try:
        # Use SDK client - handles field updates and group fetching
        consumer_response = _client.consumers.update(consumer_id, consumer_data)
        return consumer_response
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


@ConsumersRouter.delete(
    "/consumers/{consumer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Consumers"]
)
async def delete_consumer(consumer_id: UUID):
    """Delete a consumer"""
    try:
        # Use SDK client - handles deletion
        _client.consumers.delete(consumer_id)
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