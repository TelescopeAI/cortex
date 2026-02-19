"""
Hook manager for SDK operations.

Provides high-level API for managing hooks across all managers.
"""
from typing import List, Optional

from cortex.sdk.hooks.base import BaseHook, HookRegistry
from cortex.sdk.hooks.contexts import EventContext


class HookManager:
    """
    Manages hooks for all SDK operations.

    Provides:
    - Dynamic add/remove of hooks
    - Filtering by manager, operation, event type
    - Hook enable/disable
    - Bulk operations

    Examples:
        >>> manager = HookManager()
        >>> manager.add_hook(LoggingHook(), priority=10)
        >>> manager.add_hook(MetricsHook(), priority=20)
        >>> context = manager.emit_event(context)
    """

    def __init__(self):
        self._registry = HookRegistry()

    def add_hook(self, hook: BaseHook, priority: int = 100) -> None:
        """
        Add a hook to the registry.

        Args:
            hook: Hook instance
            priority: Hook priority (lower = runs first)

        Examples:
            >>> manager = HookManager()
            >>> manager.add_hook(LoggingHook(), priority=10)
            >>> manager.add_hook(MetricsHook(), priority=20)
        """
        self._registry.register(hook, priority)

    def remove_hook(self, hook_name: str) -> bool:
        """
        Remove a hook by name.

        Args:
            hook_name: Name of hook to remove

        Returns:
            True if removed successfully

        Examples:
            >>> manager.remove_hook("LoggingHook")
            True
        """
        return self._registry.unregister(hook_name)

    def get_hook(self, name: str) -> Optional[BaseHook]:
        """
        Get hook by name.

        Args:
            name: Hook name

        Returns:
            Hook instance or None

        Examples:
            >>> hook = manager.get_hook("MetricsHook")
            >>> stats = hook.get_stats()
        """
        return self._registry.get_hook(name)

    def enable_hook(self, hook_name: str) -> bool:
        """
        Enable a hook.

        Args:
            hook_name: Hook name

        Returns:
            True if hook found and enabled

        Examples:
            >>> manager.enable_hook("LoggingHook")
            True
        """
        hook = self.get_hook(hook_name)
        if hook:
            hook.enable()
            return True
        return False

    def disable_hook(self, hook_name: str) -> bool:
        """
        Disable a hook (temporarily).

        Args:
            hook_name: Hook name

        Returns:
            True if hook found and disabled

        Examples:
            >>> manager.disable_hook("LoggingHook")
            True
        """
        hook = self.get_hook(hook_name)
        if hook:
            hook.disable()
            return True
        return False

    def emit_event(self, context: EventContext) -> EventContext:
        """
        Emit event to all registered hooks.

        Args:
            context: Event context

        Returns:
            Modified context

        Examples:
            >>> context = manager.emit_event(context)
        """
        return self._registry.emit(context)

    def clear_hooks(self) -> None:
        """
        Remove all hooks.

        Examples:
            >>> manager.clear_hooks()
        """
        self._registry.clear()

    @property
    def hooks(self) -> List[BaseHook]:
        """
        Get all registered hooks.

        Returns:
            List of hooks ordered by priority

        Examples:
            >>> hooks = manager.hooks
            >>> print(f"Registered: {len(hooks)} hooks")
        """
        return self._registry.hooks
