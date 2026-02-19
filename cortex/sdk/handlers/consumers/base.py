"""
Consumers handler - routes to direct or remote based on mode.

Provides unified interface for consumer operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.consumer.consumers import (
    ConsumerCreateRequest,
    ConsumerUpdateRequest
)
from cortex.sdk.schemas.responses.consumers.consumers import ConsumerResponse
from . import direct, remote


class ConsumersHandler:
    """
    Handler for consumers operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = ConsumersHandler(mode=ConnectionMode.DIRECT)
        >>> consumers = handler.list(environment_id=env_id)

        API mode:
        >>> handler = ConsumersHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> consumers = handler.list(environment_id=env_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize consumers handler.

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
            operation: Operation name (e.g., "consumers.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="consumers",
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

    def create(self, request: ConsumerCreateRequest) -> ConsumerResponse:
        """
        Create a new consumer.

        Args:
            request: Consumer creation request

        Returns:
            Created consumer response

        Examples:
            >>> from cortex.sdk.schemas.requests.consumer.consumers import ConsumerCreateRequest
            >>> request = ConsumerCreateRequest(
            ...     environment_id=env_id,
            ...     first_name="John",
            ...     last_name="Doe",
            ...     email="john.doe@example.com"
            ... )
            >>> consumer = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="consumers.create",
            event_name=CortexEvents.CONSUMER_CREATED,
            func=lambda: (
                direct.create_consumer(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_consumer(self.http_client, request)
            ),
            environment_id=request.environment_id,
        )

    def get(self, consumer_id: UUID) -> ConsumerResponse:
        """
        Get a consumer by ID.

        Args:
            consumer_id: Consumer ID

        Returns:
            Consumer response

        Examples:
            >>> consumer = handler.get(consumer_id)
            >>> print(consumer.email)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_consumer(consumer_id)
        else:
            return remote.get_consumer(self.http_client, consumer_id)

    def list(self, environment_id: UUID) -> List[ConsumerResponse]:
        """
        List consumers in an environment.

        Args:
            environment_id: Environment ID

        Returns:
            List of consumer responses

        Examples:
            >>> consumers = handler.list(environment_id=env_id)
            >>> for consumer in consumers:
            ...     print(consumer.email)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_consumers(environment_id)
        else:
            return remote.list_consumers(self.http_client, environment_id)

    def update(
        self, consumer_id: UUID, request: ConsumerUpdateRequest
    ) -> ConsumerResponse:
        """
        Update a consumer.

        Args:
            consumer_id: Consumer ID
            request: Update request

        Returns:
            Updated consumer response

        Examples:
            >>> from cortex.sdk.schemas.requests.consumer.consumers import ConsumerUpdateRequest
            >>> request = ConsumerUpdateRequest(
            ...     first_name="Jane"
            ... )
            >>> consumer = handler.update(consumer_id, request)
        """
        return self._execute_with_hooks(
            operation="consumers.update",
            event_name=CortexEvents.CONSUMER_UPDATED,
            func=lambda: (
                direct.update_consumer(consumer_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_consumer(self.http_client, consumer_id, request)
            ),
            consumer_id=consumer_id,
        )

    def delete(self, consumer_id: UUID) -> None:
        """
        Delete a consumer.

        Args:
            consumer_id: Consumer ID

        Examples:
            >>> handler.delete(consumer_id)
        """
        self._execute_with_hooks(
            operation="consumers.delete",
            event_name=CortexEvents.CONSUMER_DELETED,
            func=lambda: (
                direct.delete_consumer(consumer_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_consumer(self.http_client, consumer_id)
            ),
            consumer_id=consumer_id,
        )
