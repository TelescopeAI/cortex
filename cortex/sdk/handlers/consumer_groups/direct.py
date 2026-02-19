"""
Consumer groups direct handler - Core service calls.

Handles consumer group operations in Direct mode.
"""
from typing import List
from uuid import UUID

from cortex.core.consumers.groups import ConsumerGroup
from cortex.core.consumers.db.group_service import ConsumerGroupCRUD
from cortex.sdk.schemas.requests.consumer.groups import (
    ConsumerGroupCreateRequest,
    ConsumerGroupUpdateRequest,
    ConsumerGroupMembershipRequest
)
from cortex.sdk.schemas.responses.consumers.groups import (
    ConsumerGroupResponse,
    ConsumerGroupDetailResponse,
    ConsumerGroupMembershipResponse
)
from cortex.sdk.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_consumer_group(request: ConsumerGroupCreateRequest) -> ConsumerGroupResponse:
    """
    Create a new consumer group - direct Core service call.

    Args:
        request: Consumer group creation request

    Returns:
        Created consumer group response
    """
    try:
        group = ConsumerGroup(
            environment_id=request.environment_id,
            name=request.name,
            description=request.description,
            alias=request.alias,
            properties=request.properties
        )
        created_group = ConsumerGroupCRUD.add_consumer_group(group)
        return ConsumerGroupResponse(**created_group.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_consumer_group(group_id: UUID) -> ConsumerGroupResponse:
    """
    Get a consumer group by ID - direct Core service call.

    Args:
        group_id: Consumer group ID

    Returns:
        Consumer group response
    """
    try:
        group = ConsumerGroupCRUD.get_consumer_group(group_id)
        return ConsumerGroupResponse(**group.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_consumer_group_with_members(group_id: UUID) -> ConsumerGroupDetailResponse:
    """
    Get a consumer group with its members - direct Core service call.

    Args:
        group_id: Consumer group ID

    Returns:
        Consumer group detail response with members
    """
    try:
        group, consumers = ConsumerGroupCRUD.get_consumer_group_with_consumers(group_id)

        # Get groups for each consumer
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
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_consumer_groups(environment_id: UUID) -> List[ConsumerGroupResponse]:
    """
    List consumer groups in an environment - direct Core service call.

    Args:
        environment_id: Environment ID

    Returns:
        List of consumer group responses
    """
    try:
        groups = ConsumerGroupCRUD.get_consumer_groups_by_environment(environment_id)
        return [ConsumerGroupResponse(**g.model_dump()) for g in groups]
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_consumer_group(
    group_id: UUID,
    request: ConsumerGroupUpdateRequest
) -> ConsumerGroupResponse:
    """
    Update a consumer group - direct Core service call.

    Args:
        group_id: Consumer group ID
        request: Update request

    Returns:
        Updated consumer group response
    """
    try:
        # Get existing group
        existing_group = ConsumerGroupCRUD.get_consumer_group(group_id)

        # Update only provided fields
        if request.name is not None:
            existing_group.name = request.name
        if request.description is not None:
            existing_group.description = request.description
        if request.alias is not None:
            existing_group.alias = request.alias
        # Allow null values for properties to clear them
        if hasattr(request, 'properties'):
            existing_group.properties = request.properties

        updated_group = ConsumerGroupCRUD.update_consumer_group(existing_group)
        return ConsumerGroupResponse(**updated_group.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_consumer_group(group_id: UUID) -> None:
    """
    Delete a consumer group - direct Core service call.

    Args:
        group_id: Consumer group ID
    """
    try:
        success = ConsumerGroupCRUD.delete_consumer_group(group_id)
        if not success:
            raise CortexNotFoundError(f"Consumer group with ID {group_id} not found")
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def add_consumer_to_group(group_id: UUID, request: ConsumerGroupMembershipRequest) -> dict:
    """
    Add a consumer to a group - direct Core service call.

    Args:
        group_id: Consumer group ID
        request: Membership request

    Returns:
        Success message
    """
    try:
        ConsumerGroupCRUD.add_consumer_to_group(group_id, request.consumer_id)
        return {"status": "success", "message": "Consumer added to group"}
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def remove_consumer_from_group(group_id: UUID, consumer_id: UUID) -> dict:
    """
    Remove a consumer from a group - direct Core service call.

    Args:
        group_id: Consumer group ID
        consumer_id: Consumer ID

    Returns:
        Success message
    """
    try:
        result = ConsumerGroupCRUD.remove_consumer_from_group(group_id, consumer_id)
        if result:
            return {"status": "success", "message": "Consumer removed from group"}
        return {"status": "success", "message": "Consumer was not a member of the group"}
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def check_consumer_in_group(group_id: UUID, consumer_id: UUID) -> ConsumerGroupMembershipResponse:
    """
    Check if a consumer is in a group - direct Core service call.

    Args:
        group_id: Consumer group ID
        consumer_id: Consumer ID

    Returns:
        Membership status response
    """
    try:
        is_member = ConsumerGroupCRUD.is_consumer_in_group(group_id, consumer_id)
        return ConsumerGroupMembershipResponse(is_member=is_member)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
