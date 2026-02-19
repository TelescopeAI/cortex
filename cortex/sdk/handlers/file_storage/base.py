"""
File storage handler - routes to direct or remote based on mode.

Provides unified interface for file storage operations with hook integration.
"""
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import FileStorageEventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from . import direct, remote


class FileStorageHandler:
    """
    Handler for file storage operations - routes to direct or remote based on mode.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = FileStorageHandler(mode=ConnectionMode.DIRECT)
        >>> result = handler.upload(environment_id=env_id, files=[(name, content)])

        API mode:
        >>> handler = FileStorageHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> result = handler.upload(environment_id=env_id, files=[(name, content)])
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize file storage handler.

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
            operation: Operation name (e.g., "file_storage.upload")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = FileStorageEventContext(
            operation=operation,
            manager="file_storage",
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

    def upload(
        self,
        environment_id: UUID,
        files: List[Tuple[str, bytes]],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Upload files to storage.

        Args:
            environment_id: Environment ID
            files: List of (filename, content) tuples
            overwrite: Whether to overwrite existing files (default: False)

        Returns:
            Dictionary with uploaded file information

        Examples:
            >>> with open("data.csv", "rb") as f:
            ...     content = f.read()
            >>> result = handler.upload(
            ...     environment_id=env_id,
            ...     files=[("data.csv", content)]
            ... )
            >>> print(result["file_ids"])
        """
        return self._execute_with_hooks(
            operation="file_storage.upload",
            event_name=CortexEvents.FILE_UPLOADED,
            func=lambda: (
                direct.upload_files(environment_id, files, overwrite)
                if self.mode == ConnectionMode.DIRECT
                else remote.upload_files(self.http_client, environment_id, files, overwrite)
            ),
            environment_id=environment_id,
        )

    def list(
        self,
        environment_id: UUID,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List uploaded files in an environment.

        Args:
            environment_id: Environment ID
            limit: Optional limit on number of files

        Returns:
            Dictionary with list of files

        Examples:
            >>> result = handler.list(environment_id=env_id, limit=10)
            >>> for file in result["files"]:
            ...     print(file["name"])
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.list_files(environment_id, limit)
        else:
            return remote.list_files(self.http_client, environment_id, limit)

    def delete(
        self,
        file_id: UUID,
        environment_id: UUID,
        cascade: bool = False
    ) -> None:
        """
        Delete a file from storage.

        Args:
            file_id: File ID to delete
            environment_id: Environment ID
            cascade: If true, delete dependent data sources and metrics (default: False)

        Examples:
            >>> handler.delete(file_id, environment_id=env_id)
            >>> # With cascade to delete dependencies
            >>> handler.delete(file_id, environment_id=env_id, cascade=True)
        """
        self._execute_with_hooks(
            operation="file_storage.delete",
            event_name=CortexEvents.FILE_DELETED,
            func=lambda: (
                direct.delete_file(file_id, environment_id, cascade)
                if self.mode == ConnectionMode.DIRECT
                else remote.delete_file(self.http_client, file_id, environment_id, cascade)
            ),
            file_id=file_id,
            environment_id=environment_id,
        )
