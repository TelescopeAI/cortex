from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.requests.consumer.groups import ConsumerGroupCreateRequest, ConsumerGroupUpdateRequest, \
    ConsumerGroupMembershipRequest
from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.api.schemas.responses.consumers.groups import ConsumerGroupResponse, ConsumerGroupDetailResponse, \
    ConsumerGroupMembershipResponse
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError

ConsumerGroupsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@ConsumerGroupsRouter.post(
    "/consumers/groups",
    response_model=ConsumerGroupResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Consumer Groups"]
)
async def create_consumer_group(group_data: ConsumerGroupCreateRequest):
    """Create a new consumer group"""
    try:
        group_response = _client.consumer_groups.create(group_data)
        return group_response
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


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}",
    response_model=ConsumerGroupResponse,
    tags=["Consumer Groups"]
)
async def get_consumer_group(group_id: UUID):
    """Get a consumer group by ID"""
    try:
        group_response = _client.consumer_groups.get(group_id)
        return group_response
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


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}/detail",
    response_model=ConsumerGroupDetailResponse,
    tags=["Consumer Groups"]
)
async def get_consumer_group_with_members(group_id: UUID):
    """Get a consumer group by ID with all its members"""
    try:
        group_detail_response = _client.consumer_groups.get_with_members(group_id)
        return group_detail_response
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


@ConsumerGroupsRouter.get(
    "/environments/{environment_id}/consumers/groups",
    response_model=List[ConsumerGroupResponse],
    tags=["Environments"]
)
async def list_consumer_groups(environment_id: UUID):
    """List all consumer groups in an environment"""
    try:
        groups = _client.consumer_groups.list(environment_id)
        return groups
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


@ConsumerGroupsRouter.put(
    "/consumers/groups/{group_id}",
    response_model=ConsumerGroupResponse,
    tags=["Consumer Groups"]
)
async def update_consumer_group(group_id: UUID, group_data: ConsumerGroupUpdateRequest):
    """Update a consumer group"""
    try:
        updated_group = _client.consumer_groups.update(group_id, group_data)
        return updated_group
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


@ConsumerGroupsRouter.delete(
    "/consumers/groups/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Consumer Groups"]
)
async def delete_consumer_group(group_id: UUID):
    """Delete a consumer group"""
    try:
        _client.consumer_groups.delete(group_id)
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


@ConsumerGroupsRouter.post(
    "/consumers/groups/{group_id}/members",
    status_code=status.HTTP_200_OK,
    tags=["Consumer Groups"]
)
async def add_consumer_to_group(group_id: UUID, request: ConsumerGroupMembershipRequest):
    """Add a consumer to a group"""
    try:
        _client.consumer_groups.add_member(group_id, request.consumer_id)
        return {"status": "success", "message": "Consumer added to group"}
    except CortexNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except CortexValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CortexSDKError as e:
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
        result = _client.consumer_groups.remove_member(group_id, consumer_id)
        if result:
            return {"status": "success", "message": "Consumer removed from group"}
        return {"status": "success", "message": "Consumer was not a member of the group"}
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


@ConsumerGroupsRouter.get(
    "/consumers/groups/{group_id}/members/{consumer_id}",
    response_model=ConsumerGroupMembershipResponse,
    tags=["Consumer Groups"]
)
async def check_consumer_in_group(group_id: UUID, consumer_id: UUID):
    """Check if a consumer is a member of a group"""
    try:
        is_member = _client.consumer_groups.check_membership(group_id, consumer_id)
        return ConsumerGroupMembershipResponse(is_member=is_member)
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
