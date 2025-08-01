from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.requests.consumer.groups import ConsumerGroupCreateRequest, ConsumerGroupUpdateRequest, \
    ConsumerGroupMembershipRequest
from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.api.schemas.responses.consumers.groups import ConsumerGroupResponse, ConsumerGroupDetailResponse, \
    ConsumerGroupMembershipResponse
from cortex.core.consumers.db.group_service import ConsumerGroupCRUD
from cortex.core.consumers.groups import ConsumerGroup
from cortex.core.exceptions.consumers import ConsumerDoesNotExistError, ConsumerGroupDoesNotExistError, \
    ConsumerGroupAlreadyExistsError
from cortex.core.exceptions.environments import EnvironmentDoesNotExistError

ConsumerGroupsRouter = APIRouter()


@ConsumerGroupsRouter.post(
    "/consumers/groups",
    response_model=ConsumerGroupResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Consumer Groups"]
)
async def create_consumer_group(group_data: ConsumerGroupCreateRequest):
    """Create a new consumer group"""
    try:
        group = ConsumerGroup(
            environment_id=group_data.environment_id,
            name=group_data.name,
            description=group_data.description,
            alias=group_data.alias,
            properties=group_data.properties
        )
        created_group = ConsumerGroupCRUD.add_consumer_group(group)
        return ConsumerGroupResponse(**created_group.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConsumerGroupAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}",
    response_model=ConsumerGroupResponse,
    tags=["Consumer Groups"]
)
async def get_consumer_group(group_id: UUID):
    """Get a consumer group by ID"""
    try:
        group = ConsumerGroupCRUD.get_consumer_group(group_id)
        return ConsumerGroupResponse(**group.model_dump())
    except ConsumerGroupDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}/detail",
    response_model=ConsumerGroupDetailResponse,
    tags=["Consumer Groups"]
)
async def get_consumer_group_with_members(group_id: UUID):
    """Get a consumer group by ID with all its members"""
    try:
        group, consumers = ConsumerGroupCRUD.get_consumer_group_with_consumers(group_id)
        # Get groups for each consumer
        from cortex.core.consumers.db.service import ConsumerCRUD
        consumer_responses = []
        
        for consumer in consumers:
            groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer.id)
            groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]
            
            consumer_dict = consumer.model_dump()
            consumer_dict["groups"] = groups_data
            
            consumer_responses.append(ConsumerResponse(**consumer_dict))
        
        return ConsumerGroupDetailResponse(
            **group.model_dump(),
            consumers=consumer_responses
        )
    except ConsumerGroupDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.get(
    "/environments/{environment_id}/consumers/groups",
    response_model=List[ConsumerGroupResponse],
    tags=["Environments"]
)
async def list_consumer_groups(environment_id: UUID):
    """List all consumer groups in an environment"""
    try:
        groups = ConsumerGroupCRUD.get_consumer_groups_by_environment(environment_id)
        return [ConsumerGroupResponse(**g.model_dump()) for g in groups]
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


@ConsumerGroupsRouter.put(
    "/consumers/groups/{group_id}",
    response_model=ConsumerGroupResponse,
    tags=["Consumer Groups"]
)
async def update_consumer_group(group_id: UUID, group_data: ConsumerGroupUpdateRequest):
    """Update a consumer group"""
    try:
        # Get existing group
        existing_group = ConsumerGroupCRUD.get_consumer_group(group_id)

        # Update only provided fields
        if group_data.name is not None:
            existing_group.name = group_data.name
        if group_data.description is not None:
            existing_group.description = group_data.description
        if group_data.alias is not None:
            existing_group.alias = group_data.alias
        # Allow null values for properties to clear them
        if hasattr(group_data, 'properties'):
            existing_group.properties = group_data.properties

        updated_group = ConsumerGroupCRUD.update_consumer_group(existing_group)
        return ConsumerGroupResponse(**updated_group.model_dump())
    except ConsumerGroupDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.delete(
    "/consumers/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Consumer Groups"]
)
async def delete_consumer_group(group_id: UUID):
    """Delete a consumer group"""
    try:
        if ConsumerGroupCRUD.delete_consumer_group(group_id):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete consumer group"
        )
    except ConsumerGroupDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.post(
    "/consumers/groups/{group_id}/members",
    status_code=status.HTTP_200_OK,
    tags=["Consumer Groups"]
)
async def add_consumer_to_group(group_id: UUID, request: ConsumerGroupMembershipRequest):
    """Add a consumer to a group"""
    try:
        ConsumerGroupCRUD.add_consumer_to_group(group_id, request.consumer_id)
        return {"status": "success", "message": "Consumer added to group"}
    except (ConsumerGroupDoesNotExistError, ConsumerDoesNotExistError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.delete(
    "/consumers/groups/{group_id}/members/{consumer_id}",
    status_code=status.HTTP_200_OK,
    tags=["Consumer Groups"]
)
async def remove_consumer_from_group(group_id: UUID, consumer_id: UUID):
    """Remove a consumer from a group"""
    try:
        result = ConsumerGroupCRUD.remove_consumer_from_group(group_id, consumer_id)
        if result:
            return {"status": "success", "message": "Consumer removed from group"}
        return {"status": "success", "message": "Consumer was not a member of the group"}
    except (ConsumerGroupDoesNotExistError, ConsumerDoesNotExistError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}/members/{consumer_id}",
    response_model=ConsumerGroupMembershipResponse,
    tags=["Consumer Groups"]
)
async def check_consumer_in_group(group_id: UUID, consumer_id: UUID):
    """Check if a consumer is a member of a group"""
    try:
        is_member = ConsumerGroupCRUD.is_consumer_in_group(group_id, consumer_id)
        return ConsumerGroupMembershipResponse(is_member=is_member)
    except (ConsumerGroupDoesNotExistError, ConsumerDoesNotExistError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )