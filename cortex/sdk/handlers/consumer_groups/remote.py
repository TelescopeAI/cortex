"""
Consumer groups remote handler - HTTP API calls.

Handles consumer group operations in API mode.
"""
from typing import List
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
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


def create_consumer_group(
    client: CortexHTTPClient,
    request: ConsumerGroupCreateRequest
) -> ConsumerGroupResponse:
    """
    Create a new consumer group - HTTP API call.

    Args:
        client: HTTP client
        request: Consumer group creation request

    Returns:
        Created consumer group response
    """
    response = client.post("/consumers/groups", data=request.model_dump())
    return ConsumerGroupResponse(**response)


def get_consumer_group(
    client: CortexHTTPClient,
    group_id: UUID
) -> ConsumerGroupResponse:
    """
    Get a consumer group by ID - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID

    Returns:
        Consumer group response
    """
    response = client.get(f"/consumers/groups/{group_id}")
    return ConsumerGroupResponse(**response)


def get_consumer_group_with_members(
    client: CortexHTTPClient,
    group_id: UUID
) -> ConsumerGroupDetailResponse:
    """
    Get a consumer group with its members - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID

    Returns:
        Consumer group detail response with members
    """
    response = client.get(f"/consumers/groups/{group_id}/detail")
    return ConsumerGroupDetailResponse(**response)


def list_consumer_groups(
    client: CortexHTTPClient,
    environment_id: UUID
) -> List[ConsumerGroupResponse]:
    """
    List consumer groups in an environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID

    Returns:
        List of consumer group responses
    """
    response = client.get(f"/environments/{environment_id}/consumers/groups")
    return [ConsumerGroupResponse(**group) for group in response]


def update_consumer_group(
    client: CortexHTTPClient,
    group_id: UUID,
    request: ConsumerGroupUpdateRequest
) -> ConsumerGroupResponse:
    """
    Update a consumer group - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID
        request: Update request

    Returns:
        Updated consumer group response
    """
    response = client.put(f"/consumers/groups/{group_id}", data=request.model_dump())
    return ConsumerGroupResponse(**response)


def delete_consumer_group(
    client: CortexHTTPClient,
    group_id: UUID
) -> None:
    """
    Delete a consumer group - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID
    """
    client.delete(f"/consumers/groups/{group_id}")


def add_consumer_to_group(
    client: CortexHTTPClient,
    group_id: UUID,
    request: ConsumerGroupMembershipRequest
) -> dict:
    """
    Add a consumer to a group - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID
        request: Membership request

    Returns:
        Success message
    """
    response = client.post(f"/consumers/groups/{group_id}/members", data=request.model_dump())
    return response


def remove_consumer_from_group(
    client: CortexHTTPClient,
    group_id: UUID,
    consumer_id: UUID
) -> dict:
    """
    Remove a consumer from a group - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID
        consumer_id: Consumer ID

    Returns:
        Success message
    """
    response = client.delete(f"/consumers/groups/{group_id}/members/{consumer_id}")
    return response


def check_consumer_in_group(
    client: CortexHTTPClient,
    group_id: UUID,
    consumer_id: UUID
) -> ConsumerGroupMembershipResponse:
    """
    Check if a consumer is in a group - HTTP API call.

    Args:
        client: HTTP client
        group_id: Consumer group ID
        consumer_id: Consumer ID

    Returns:
        Membership status response
    """
    response = client.get(f"/consumers/groups/{group_id}/members/{consumer_id}")
    return ConsumerGroupMembershipResponse(**response)
