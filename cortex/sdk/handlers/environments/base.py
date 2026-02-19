"""
Environments handler - routes to direct or remote based on mode.

Provides unified interface for environment operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.environments import (
    EnvironmentCreateRequest,
    EnvironmentUpdateRequest
)
from cortex.sdk.schemas.responses.environments import EnvironmentResponse
from . import direct, remote


class EnvironmentsHandler:
    """
    Handler for environments operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = EnvironmentsHandler(mode=ConnectionMode.DIRECT)
        >>> environments = handler.list(workspace_id=ws_id)

        API mode:
        >>> handler = EnvironmentsHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> environments = handler.list(workspace_id=ws_id)
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize environments handler.

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
            operation: Operation name (e.g., "environments.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="environments",
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

    def create(self, request: EnvironmentCreateRequest) -> EnvironmentResponse:
        """
        Create a new environment.

        Args:
            request: Environment creation request

        Returns:
            Created environment response

        Examples:
            >>> from cortex.sdk.schemas.requests.environments import EnvironmentCreateRequest
            >>> request = EnvironmentCreateRequest(
            ...     workspace_id=workspace_id,
            ...     name="Production",
            ...     description="Production environment"
            ... )
            >>> environment = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="environments.create",
            event_name=CortexEvents.ENVIRONMENT_CREATED,
            func=lambda: (
                direct.create_environment(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_environment(self.http_client, request)
            ),
            workspace_id=request.workspace_id,
        )

    def get(self, environment_id: UUID) -> EnvironmentResponse:
        """
        Get an environment by ID.

        Args:
            environment_id: Environment ID

        Returns:
            Environment response

        Examples:
            >>> environment = handler.get(environment_id)
            >>> print(environment.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_environment(environment_id)
        else:
            return remote.get_environment(self.http_client, environment_id)

    def list(self, workspace_id: UUID) -> List[EnvironmentResponse]:
        """
        List environments in a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of environment responses

        Examples:
            >>> environments = handler.list(workspace_id=ws_id)
            >>> for environment in environments:
            ...     print(environment.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_environments(workspace_id)
        else:
            return remote.list_environments(self.http_client, workspace_id)

    def update(
        self, environment_id: UUID, request: EnvironmentUpdateRequest
    ) -> EnvironmentResponse:
        """
        Update an environment.

        Args:
            environment_id: Environment ID
            request: Update request

        Returns:
            Updated environment response

        Examples:
            >>> from cortex.sdk.schemas.requests.environments import EnvironmentUpdateRequest
            >>> request = EnvironmentUpdateRequest(
            ...     name="Staging",
            ...     description="Staging environment"
            ... )
            >>> environment = handler.update(environment_id, request)
        """
        return self._execute_with_hooks(
            operation="environments.update",
            event_name=CortexEvents.ENVIRONMENT_UPDATED,
            func=lambda: (
                direct.update_environment(environment_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_environment(self.http_client, environment_id, request)
            ),
            environment_id=environment_id,
        )

    def delete(self, environment_id: UUID) -> None:
        """
        Delete an environment.

        Args:
            environment_id: Environment ID

        Examples:
            >>> handler.delete(environment_id)
        """
        self._execute_with_hooks(
            operation="environments.delete",
            event_name=CortexEvents.ENVIRONMENT_DELETED,
            func=lambda: (
                direct.delete_environment(environment_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_environment(self.http_client, environment_id)
            ),
            environment_id=environment_id,
        )
