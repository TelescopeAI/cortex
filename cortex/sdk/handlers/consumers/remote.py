"""
Consumers remote handler - HTTP API calls.

Handles consumer operations in API mode.
"""
from typing import List
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.consumer.consumers import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest
)
from cortex.sdk.schemas.responses.consumers.consumers import ConsumerResponse


def create_consumer(
    client: CortexHTTPClient,
    request: ConsumerCreateRequest
) -> ConsumerResponse:
    """
    Create a new consumer - HTTP API call.

    Args:
        client: HTTP client
        request: Consumer creation request

    Returns:
        Created consumer response
    """
    response = client.post("/consumers", data=request.model_dump())
    return ConsumerResponse(**response)


def get_consumer(
    client: CortexHTTPClient,
    consumer_id: UUID
) -> ConsumerResponse:
    """
    Get a consumer by ID - HTTP API call.

    Args:
        client: HTTP client
        consumer_id: Consumer ID

    Returns:
        Consumer response
    """
    response = client.get(f"/consumers/{consumer_id}")
    return ConsumerResponse(**response)


def list_consumers(
    client: CortexHTTPClient,
    environment_id: UUID
) -> List[ConsumerResponse]:
    """
    List consumers in an environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID

    Returns:
        List of consumer responses
    """
    response = client.get(f"/environments/{environment_id}/consumers")
    return [ConsumerResponse(**consumer) for consumer in response]


def update_consumer(
    client: CortexHTTPClient,
    consumer_id: UUID,
    request: ConsumerUpdateRequest
) -> ConsumerResponse:
    """
    Update a consumer - HTTP API call.

    Args:
        client: HTTP client
        consumer_id: Consumer ID
        request: Update request

    Returns:
        Updated consumer response
    """
    response = client.put(f"/consumers/{consumer_id}", data=request.model_dump())
    return ConsumerResponse(**response)


def delete_consumer(
    client: CortexHTTPClient,
    consumer_id: UUID
) -> None:
    """
    Delete a consumer - HTTP API call.

    Args:
        client: HTTP client
        consumer_id: Consumer ID
    """
    client.delete(f"/consumers/{consumer_id}")
