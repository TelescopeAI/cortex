"""
Admin handler - routes to direct or remote based on mode.

Provides unified interface for admin operations with hook integration.
"""
from typing import Optional, Dict, Any

from cortex.sdk.config import ConnectionMode
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import CortexEvents, HookEventType
from cortex.sdk.schemas.responses.admin.cache import (
    CacheEvictionResponse,
    CacheStatusResponse
)
from . import direct, remote


class AdminHandler:
    """
    Handler for admin operations - routes to direct or remote based on mode.

    Provides cache management and other admin operations.

    Attributes:
        mode: Connection mode (DIRECT or API)
        http_client: HTTP client for API mode
        _hooks: Hook manager for event emission
        _context: Client context (workspace_id, environment_id)

    Examples:
        Direct mode:
        >>> handler = AdminHandler(mode=ConnectionMode.DIRECT)
        >>> status = handler.get_cache_status()

        API mode:
        >>> handler = AdminHandler(
        ...     mode=ConnectionMode.API,
        ...     http_client=http_client
        ... )
        >>> result = handler.evict_cache()
    """

    def __init__(
        self,
        mode: ConnectionMode,
        http_client: Optional[CortexHTTPClient] = None,
        hooks: Optional[HookManager] = None,
        client_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize admin handler.

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
            operation: Operation name (e.g., "admin.evict_cache")
            event_name: Event type from CortexEvents
            func: Operation function to execute
            **context_kwargs: Additional context for hooks

        Returns:
            Operation result
        """
        # BEFORE hook
        context = EventContext(
            operation=operation,
            manager="admin",
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

    def evict_cache(self) -> CacheEvictionResponse:
        """
        Evict LRU cache entries to free space.

        This operation should be called by the jobs server in distributed deployments
        to trigger cache eviction on the API server's local SSD.

        Returns:
            Cache eviction response with number of evicted files

        Examples:
            >>> result = handler.evict_cache()
            >>> print(f"Evicted {result.evicted_files} files")
        """
        return self._execute_with_hooks(
            operation="admin.evict_cache",
            event_name=CortexEvents.CACHE_CLEARED,
            func=lambda: (
                direct.evict_cache()
                if self.mode == ConnectionMode.DIRECT
                else remote.evict_cache(self.http_client)
            ),
        )

    def get_cache_status(self) -> CacheStatusResponse:
        """
        Get current cache statistics.

        This operation provides information about the current state of the local SSD cache,
        useful for monitoring and debugging.

        Returns:
            Cache status response with size and entry count

        Examples:
            >>> status = handler.get_cache_status()
            >>> print(f"Cache size: {status.cache_size_gb:.2f} GB / {status.max_size_gb} GB")
            >>> print(f"Entries: {status.entries_count}")
        """
        if self.mode == ConnectionMode.DIRECT:
            return direct.get_cache_status()
        else:
            return remote.get_cache_status(self.http_client)
