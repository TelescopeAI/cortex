"""
Consumers direct handler - Core service calls.

Handles consumer operations in Direct mode.
"""
from typing import List
from uuid import UUID

from cortex.core.consumers.consumer import Consumer
from cortex.core.consumers.db.service import ConsumerCRUD
from cortex.core.consumers.db.group_service import ConsumerGroupCRUD
from cortex.sdk.schemas.requests.consumer.consumers import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest
)
from cortex.sdk.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_consumer(request: ConsumerCreateRequest) -> ConsumerResponse:
    """
    Create a new consumer - direct Core service call.

    Args:
        request: Consumer creation request

    Returns:
        Created consumer response
    """
    try:
        consumer = Consumer(
            environment_id=request.environment_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            organization=request.organization,
            properties=request.properties
        )
        created_consumer = ConsumerCRUD.add_consumer(consumer)
        consumer_dict = created_consumer.model_dump()
        consumer_dict["groups"] = []  # New consumer has no groups
        return ConsumerResponse(**consumer_dict)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_consumer(consumer_id: UUID) -> ConsumerResponse:
    """
    Get a consumer by ID - direct Core service call.

    Args:
        consumer_id: Consumer ID

    Returns:
        Consumer response
    """
    try:
        consumer = ConsumerCRUD.get_consumer(consumer_id)

        # Get groups for this consumer
        groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer_id)
        groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]

        consumer_dict = consumer.model_dump()
        consumer_dict["groups"] = groups_data

        return ConsumerResponse(**consumer_dict)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_consumers(environment_id: UUID) -> List[ConsumerResponse]:
    """
    List consumers in an environment - direct Core service call.

    Args:
        environment_id: Environment ID

    Returns:
        List of consumer responses
    """
    try:
        consumers = ConsumerCRUD.get_consumers_by_environment(environment_id)

        # Get groups for each consumer
        consumer_responses = []

        for consumer in consumers:
            groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer.id)
            groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]

            consumer_dict = consumer.model_dump()
            consumer_dict["groups"] = groups_data

            consumer_responses.append(ConsumerResponse(**consumer_dict))

        return consumer_responses
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_consumer(
    consumer_id: UUID,
    request: ConsumerUpdateRequest
) -> ConsumerResponse:
    """
    Update a consumer - direct Core service call.

    Args:
        consumer_id: Consumer ID
        request: Update request

    Returns:
        Updated consumer response
    """
    try:
        # Get existing consumer first
        existing_consumer = ConsumerCRUD.get_consumer(consumer_id)

        # Update only the fields that are provided
        if request.first_name is not None:
            existing_consumer.first_name = request.first_name
        if request.last_name is not None:
            existing_consumer.last_name = request.last_name
        if request.email is not None:
            existing_consumer.email = request.email
        if request.organization is not None:
            existing_consumer.organization = request.organization
        # Allow null values for properties to clear them
        if hasattr(request, 'properties'):
            existing_consumer.properties = request.properties

        updated_consumer = ConsumerCRUD.update_consumer(existing_consumer)

        # Get groups for this consumer
        groups = ConsumerGroupCRUD.get_groups_for_consumer(consumer_id)
        groups_data = [{"id": str(g.id), "name": g.name, "description": g.description} for g in groups]

        consumer_dict = updated_consumer.model_dump()
        consumer_dict["groups"] = groups_data

        return ConsumerResponse(**consumer_dict)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_consumer(consumer_id: UUID) -> None:
    """
    Delete a consumer - direct Core service call.

    Args:
        consumer_id: Consumer ID
    """
    try:
        success = ConsumerCRUD.delete_consumer(consumer_id)
        if not success:
            raise CortexNotFoundError(f"Consumer with ID {consumer_id} not found")
    except Exception as e:
        raise CoreExceptionMapper().map(e)
