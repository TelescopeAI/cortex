"""
Consumer groups handler - routes to direct or remote based on mode.

Provides unified interface for consumer group operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
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
from . import direct, remote


class ConsumerGroupsHandler:
    """
    Handler for consumer groups operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = ConsumerGroupsHandler(mode=ConnectionMode.DIRECT)
        >>> groups = handler.list(environment_id=env_id)

        API mode:
        >>> handler = ConsumerGroupsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> groups = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize consumer groups handler.

        Args:
            mode: Connection mode (DIRECT or API)
            http_client: HTTP client instance (required for API mode)
            hooks: Hook manager for event emission
            client_context: Client context (workspace_id, environment_id)
        """
        self.mode = mode
        self.http_client = http_client
        self._hooks = hooks or HookManager()
        self._context = client_context or {}

    def _execute_with_hooks(
        self, operation: str, event_name: CortexEvents, func, **context_kwargs
    ):
        """
        Execute operation with hook lifecycle.

        Emits BEFORE → operation → AFTER (or ERROR) events.

        Args:
            operation: Operation name (e.g., "consumer_groups.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="consumer_groups",
            action=operation.split(".")[-1],
            event_type=HookEventType.BEFORE,
            event_name=event_name,
            params=context_kwargs,
            **context_kwargs,
        )
        context = self._hooks.emit_event(context)

        try:
            # Execute operation
            result = func()

            # AFTER hook
            context.event_type = HookEventType.AFTER
            context.result = result
            self._hooks.emit_event(context)

            return result
        except Exception as e:
            # ERROR hook
            context.event_type = HookEventType.ERROR
            context.error = e
            self._hooks.emit_event(context)
            raise

    def create(self, request: ConsumerGroupCreateRequest) -> ConsumerGroupResponse:
        """
        Create a new consumer group.

        Args:
            request: Consumer group creation request

        Returns:
            Created consumer group response

        Examples:
            >>> from cortex.sdk.schemas.requests.consumer.groups import ConsumerGroupCreateRequest
            >>> request = ConsumerGroupCreateRequest(
            ...     environment_id=env_id,
            ...     name="Premium Users",
            ...     description="Premium tier customers"
            ... )
            >>> group = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="consumer_groups.create",
            event_name=CortexEvents.CONSUMER_GROUP_CREATED,
            func=lambda: (
                direct.create_consumer_group(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_consumer_group(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def get(self, group_id: UUID) -> ConsumerGroupResponse:
        """
        Get a consumer group by ID.

        Args:
            group_id: Consumer group ID

        Returns:
            Consumer group response

        Examples:
            >>> group = handler.get(group_id)
            >>> print(group.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_consumer_group(group_id)
        else:
            return remote.get_consumer_group(self.http_client, group_id)

    def get_with_members(self, group_id: UUID) -> ConsumerGroupDetailResponse:
        """
        Get a consumer group with its members.

        Args:
            group_id: Consumer group ID

        Returns:
            Consumer group detail response with members

        Examples:
            >>> group = handler.get_with_members(group_id)
            >>> for consumer in group.consumers:
            ...     print(consumer.email)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_consumer_group_with_members(group_id)
        else:
            return remote.get_consumer_group_with_members(self.http_client, group_id)

    def list(self, environment_id: UUID) -> List[ConsumerGroupResponse]:
        """
        List consumer groups in an environment.

        Args:
            environment_id: Environment ID

        Returns:
            List of consumer group responses

        Examples:
            >>> groups = handler.list(environment_id=env_id)
            >>> for group in groups:
            ...     print(group.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_consumer_groups(environment_id)
        else:
            return remote.list_consumer_groups(self.http_client, environment_id)

    def update(
        self, group_id: UUID, request: ConsumerGroupUpdateRequest
    ) -> ConsumerGroupResponse:
        """
        Update a consumer group.

        Args:
            group_id: Consumer group ID
            request: Update request

        Returns:
            Updated consumer group response

        Examples:
            >>> from cortex.sdk.schemas.requests.consumer.groups import ConsumerGroupUpdateRequest
            >>> request = ConsumerGroupUpdateRequest(
            ...     name="VIP Users"
            ... )
            >>> group = handler.update(group_id, request)
        """
        return self._execute_with_hooks(
            operation="consumer_groups.update",
            event_name=CortexEvents.CONSUMER_GROUP_UPDATED,
            func=lambda: (
                direct.update_consumer_group(group_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_consumer_group(self.http_client, group_id, request)
            ),
            group_id=group_id,
        )

    def delete(self, group_id: UUID) -> None:
        """
        Delete a consumer group.

        Args:
            group_id: Consumer group ID

        Examples:
            >>> handler.delete(group_id)
        """
        self._execute_with_hooks(
            operation="consumer_groups.delete",
            event_name=CortexEvents.CONSUMER_GROUP_DELETED,
            func=lambda: (
                direct.delete_consumer_group(group_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_consumer_group(self.http_client, group_id)
            ),
            group_id=group_id,
        )

    def add_member(
        self, group_id: UUID, request: ConsumerGroupMembershipRequest
    ) -> dict:
        """
        Add a consumer to a group.

        Args:
            group_id: Consumer group ID
            request: Membership request

        Returns:
            Success message

        Examples:
            >>> from cortex.sdk.schemas.requests.consumer.groups import ConsumerGroupMembershipRequest
            >>> request = ConsumerGroupMembershipRequest(consumer_id=consumer_id)
            >>> result = handler.add_member(group_id, request)
        """
        return self._execute_with_hooks(
            operation="consumer_groups.add_member",
            event_name=CortexEvents.CONSUMER_GROUP_UPDATED,
            func=lambda: (
                direct.add_consumer_to_group(group_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.add_consumer_to_group(self.http_client, group_id, request)
            ),
            group_id=group_id,
        )

    def remove_member(self, group_id: UUID, consumer_id: UUID) -> dict:
        """
        Remove a consumer from a group.

        Args:
            group_id: Consumer group ID
            consumer_id: Consumer ID

        Returns:
            Success message

        Examples:
            >>> result = handler.remove_member(group_id, consumer_id)
        """
        return self._execute_with_hooks(
            operation="consumer_groups.remove_member",
            event_name=CortexEvents.CONSUMER_GROUP_UPDATED,
            func=lambda: (
                direct.remove_consumer_from_group(group_id, consumer_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.remove_consumer_from_group(self.http_client, group_id, consumer_id)
            ),
            group_id=group_id,
        )

    def check_membership(
        self, group_id: UUID, consumer_id: UUID
    ) -> ConsumerGroupMembershipResponse:
        """
        Check if a consumer is a member of a group.

        Args:
            group_id: Consumer group ID
            consumer_id: Consumer ID

        Returns:
            Membership status response

        Examples:
            >>> status = handler.check_membership(group_id, consumer_id)
            >>> if status.is_member:
            ...     print("Consumer is a member")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.check_consumer_in_group(group_id, consumer_id)
        else:
            return remote.check_consumer_in_group(self.http_client, group_id, consumer_id)