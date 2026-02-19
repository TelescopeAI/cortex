"""
Workspaces handler - routes to direct or remote based on mode.

Provides unified interface for workspace operations with hook integration.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.requests.workspaces import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest
)
from cortex.sdk.schemas.responses.workspaces import WorkspaceResponse
from . import direct, remote


class WorkspacesHandler:
    """
    Handler for workspaces operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = WorkspacesHandler(mode=ConnectionMode.DIRECT)
        >>> workspaces = handler.list()

        API mode:
        >>> handler = WorkspacesHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> workspaces = handler.list()
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize workspaces handler.

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
            operation: Operation name (e.g., "workspaces.create")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="workspaces",
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

    def create(self, request: WorkspaceCreateRequest) -> WorkspaceResponse:
        """
        Create a new workspace.

        Args:
            request: Workspace creation request

        Returns:
            Created workspace response

        Examples:
            >>> from cortex.sdk.schemas.requests.workspaces import WorkspaceCreateRequest
            >>> request = WorkspaceCreateRequest(
            ...     name="My Workspace",
            ...     description="Workspace for analytics"
            ... )
            >>> workspace = handler.create(request)
        """
        return self._execute_with_hooks(
            operation="workspaces.create",
            event_name=CortexEvents.WORKSPACE_CREATED,
            func=lambda: (
                direct.create_workspace(request)
                if self.mode == ConnectionMode.DIRECT
                else remote.create_workspace(self.http_client, request)
            ),
        )

    def get(self, workspace_id: UUID) -> WorkspaceResponse:
        """
        Get a workspace by ID.

        Args:
            workspace_id: Workspace ID

        Returns:
            Workspace response

        Examples:
            >>> workspace = handler.get(workspace_id)
            >>> print(workspace.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_workspace(workspace_id)
        else:
            return remote.get_workspace(self.http_client, workspace_id)

    def list(self) -> List[WorkspaceResponse]:
        """
        List all workspaces.

        Returns:
            List of workspace responses

        Examples:
            >>> workspaces = handler.list()
            >>> for workspace in workspaces:
            ...     print(workspace.name)
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_workspaces()
        else:
            return remote.list_workspaces(self.http_client)

    def update(
        self, workspace_id: UUID, request: WorkspaceUpdateRequest
    ) -> WorkspaceResponse:
        """
        Update a workspace.

        Args:
            workspace_id: Workspace ID
            request: Update request

        Returns:
            Updated workspace response

        Examples:
            >>> from cortex.sdk.schemas.requests.workspaces import WorkspaceUpdateRequest
            >>> request = WorkspaceUpdateRequest(
            ...     name="Updated Workspace"
            ... )
            >>> workspace = handler.update(workspace_id, request)
        """
        return self._execute_with_hooks(
            operation="workspaces.update",
            event_name=CortexEvents.WORKSPACE_UPDATED,
            func=lambda: (
                direct.update_workspace(workspace_id, request)
                if self.mode == ConnectionMode.DIRECT
                else remote.update_workspace(self.http_client, workspace_id, request)
            ),
            workspace_id=workspace_id,
        )

    def delete(self, workspace_id: UUID) -> None:
        """
        Delete a workspace.

        Args:
            workspace_id: Workspace ID

        Examples:
            >>> handler.delete(workspace_id)
        """
        self._execute_with_hooks(
            operation="workspaces.delete",
            event_name=CortexEvents.WORKSPACE_DELETED,
            func=lambda: (
                direct.delete_workspace(workspace_id)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_workspace(self.http_client, workspace_id)
            ),
            workspace_id=workspace_id,
        )
