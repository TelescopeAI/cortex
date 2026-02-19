"""
Base manager for all resource managers.

Provides common functionality including transport access, hook integration,
error handling, and context management.
"""
from abc import ABC
from typing import Any, Callable, Dict, Optional, Type
from uuid import UUID
import logging

from cortex.sdk.transport.base import BaseTransport
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType

logger = logging.getLogger(__name__)


class BaseManager(ABC):
    """
    Abstract base class for all resource managers.

    Provides:
    - Transport access (HTTP or Direct)
    - Hook integration with BEFORE/AFTER/ERROR lifecycle
    - Context management (workspace_id, environment_id from client)
    - Error handling

    All domain-specific managers inherit from this class.

    Attributes:
        _transport: Transport instance (HTTP or Direct)
        _client: Parent CortexClient reference
        _hooks: Hook manager for event emission

    Examples:
        Creating a manager:
        >>> class MetricsManager(BaseManager):
        ...     def list(self, environment_id=None):
        ...         env_id = environment_id or self.environment_id
        ...         return self._execute_with_hooks(
        ...             operation="metrics.list",
        ...             event_name=CortexEvents.METRIC_LISTED,
        ...             event_context_class=MetricsEventContext,
        ...             func=lambda: self._transport.get("/metrics", params={"environment_id": env_id}),
        ...             environment_id=env_id
        ...         )
    """

    def __init__(
        self,
        transport: BaseTransport,
        client: Any,  # "CortexClient" - avoid circular import
        hooks: Optional[HookManager] = None,
    ):
        """
        Initialize base manager.

        Args:
            transport: Transport instance (HTTP or Direct)
            client: Parent CortexClient reference
            hooks: Hook manager for event emission
        """
        self._transport = transport
        self._client = client
        self._hooks = hooks or HookManager()

    @property
    def workspace_id(self) -> Optional[UUID]:
        """
        Get current workspace ID from client context.

        Returns:
            Workspace ID or None
        """
        return self._client.workspace_id if self._client else None

    @property
    def environment_id(self) -> Optional[UUID]:
        """
        Get current environment ID from client context.

        Returns:
            Environment ID or None
        """
        return self._client.environment_id if self._client else None

    def _execute_with_hooks(
        self,
        operation: str,
        event_name: CortexEvents,
        event_context_class: Type[EventContext],
        func: Callable[[], Any],
        **context_kwargs,
    ) -> Any:
        """
        Execute operation with hook lifecycle.

        Lifecycle:
        1. Create EventContext with operation metadata
        2. Emit BEFORE event to hooks
        3. Execute operation function
        4. Emit AFTER event with result (or ERROR event on failure)
        5. Return result

        Args:
            operation: Operation name (e.g., "metrics.create")
            event_name: Event type from CortexEvents enum
            event_context_class: EventContext subclass to use
            func: Function to execute (should return result)
            **context_kwargs: Additional context fields (metric_id, environment_id, etc.)

        Returns:
            Operation result

        Raises:
            Exception: Re-raises any exception from operation after ERROR hook

        Examples:
            >>> result = self._execute_with_hooks(
            ...     operation="metrics.create",
            ...     event_name=CortexEvents.METRIC_CREATED,
            ...     event_context_class=MetricsEventContext,
            ...     func=lambda: self._transport.post("/metrics", data=metric_data),
            ...     environment_id=env_id,
            ...     data_model_id=model_id
            ... )
        """
        # Extract manager name from class name (e.g., "MetricsManager" -> "metrics")
        manager_name = self.__class__.__name__.replace("Manager", "").lower()

        # Extract action from operation (e.g., "metrics.create" -> "create")
        action = operation.split(".")[-1] if "." in operation else operation

        # Create BEFORE context
        context = event_context_class(
            operation=operation,
            manager=manager_name,
            action=action,
            event_type=HookEventType.BEFORE,
            event_name=event_name,
            params=context_kwargs,
            **context_kwargs,
        )

        # Emit BEFORE event
        logger.debug(f"Emitting BEFORE hook: {operation}")
        context = self._hooks.emit_event(context)

        try:
            # Execute operation
            logger.debug(f"Executing operation: {operation}")
            result = func()

            # Update context for AFTER event
            context.event_type = HookEventType.AFTER
            context.result = result

            # Emit AFTER event
            logger.debug(f"Emitting AFTER hook: {operation}")
            self._hooks.emit_event(context)

            return result

        except Exception as e:
            # Update context for ERROR event
            context.event_type = HookEventType.ERROR
            context.error = e

            # Emit ERROR event
            logger.error(f"Emitting ERROR hook: {operation} - {e}")
            self._hooks.emit_event(context)

            # Re-raise exception
            raise
