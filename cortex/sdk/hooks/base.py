"""
Base hook interface and registry.

Hooks receive events from SDK operations and can:
- Log operations
- Collect metrics
- Validate inputs/outputs
- Transform data
- Send notifications
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from cortex.sdk.hooks.contexts import EventContext


class BaseHook(ABC):
    """
    Base class for all hooks.

    Hooks can subscribe to specific operations and events.

    Attributes:
        name: Hook name for identification
        _enabled: Whether hook is currently enabled

    Examples:
        >>> class MyHook(BaseHook):
        ...     def should_handle(self, context):
        ...         return context.manager == "metrics"
        ...
        ...     def handle(self, context):
        ...         print(f"Handling: {context.operation}")
        ...         return context
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize hook.

        Args:
            name: Optional name for the hook (defaults to class name)

        Examples:
            >>> hook = MyHook(name="custom-hook")
        """
        self.name = name or self.__class__.__name__
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if hook is enabled."""
        return self._enabled

    def enable(self):
        """Enable this hook."""
        self._enabled = True

    def disable(self):
        """Disable this hook (temporarily)."""
        self._enabled = False

    def should_handle(self, context: EventContext) -> bool:
        """
        Determine if this hook should handle the event.

        Override to filter events by operation, manager, etc.

        Args:
            context: Event context

        Returns:
            True if hook should handle this event

        Examples:
            >>> def should_handle(self, context):
            ...     return context.manager == "metrics" and self.enabled
        """
        return self.enabled

    @abstractmethod
    def handle(self, context: EventContext) -> Optional[EventContext]:
        """
        Handle an event.

        Args:
            context: Event context with operation details

        Returns:
            Modified context (or original). Can modify result, params, etc.
            Return None to stop event propagation (rare use case)

        Examples:
            >>> def handle(self, context):
            ...     print(f"Event: {context.event_name}")
            ...     return context
        """
        pass

    def on_error(self, error: Exception, context: EventContext) -> None:
        """
        Called if the hook itself raises an error.

        Override to handle hook errors gracefully.

        Args:
            error: Exception raised by hook
            context: Event context

        Examples:
            >>> def on_error(self, error, context):
            ...     print(f"Hook error: {error}")
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Hook {self.name} failed: {error}", exc_info=True)


class HookRegistry:
    """
    Registry for managing hooks.

    Supports:
    - Dynamic add/remove
    - Event filtering
    - Hook ordering (priority)

    Examples:
        >>> registry = HookRegistry()
        >>> registry.register(MyHook(), priority=100)
        >>> context = registry.emit(context)
    """

    def __init__(self):
        self._hooks: List[Tuple[int, BaseHook]] = []  # (priority, hook)
        self._hook_map: Dict[str, BaseHook] = {}  # name -> hook

    def register(self, hook: BaseHook, priority: int = 100) -> None:
        """
        Register a hook.

        Args:
            hook: Hook instance
            priority: Hook priority (lower = runs first)

        Examples:
            >>> registry = HookRegistry()
            >>> registry.register(LoggingHook(), priority=10)
            >>> registry.register(MetricsHook(), priority=20)
        """
        # Add to registry
        self._hooks.append((priority, hook))
        self._hooks.sort(key=lambda x: x[0])  # Sort by priority

        # Add to map for lookup
        self._hook_map[hook.name] = hook

    def unregister(self, hook_name: str) -> bool:
        """
        Unregister a hook by name.

        Args:
            hook_name: Name of hook to remove

        Returns:
            True if hook was found and removed

        Examples:
            >>> registry.unregister("MyHook")
            True
        """
        hook = self._hook_map.pop(hook_name, None)
        if hook:
            self._hooks = [(p, h) for p, h in self._hooks if h is not hook]
            return True
        return False

    def get_hook(self, name: str) -> Optional[BaseHook]:
        """
        Get hook by name.

        Args:
            name: Hook name

        Returns:
            Hook instance or None

        Examples:
            >>> hook = registry.get_hook("MetricsHook")
        """
        return self._hook_map.get(name)

    def emit(self, context: EventContext) -> EventContext:
        """
        Emit event to all registered hooks.

        Args:
            context: Event context

        Returns:
            Modified context (after all hooks)

        Examples:
            >>> context = registry.emit(context)
        """
        for priority, hook in self._hooks:
            if not hook.should_handle(context):
                continue

            try:
                result = hook.handle(context)
                if result is None:
                    # Hook stopped propagation
                    break
                context = result
            except Exception as e:
                hook.on_error(e, context)

        return context

    def clear(self) -> None:
        """
        Remove all hooks.

        Examples:
            >>> registry.clear()
        """
        self._hooks.clear()
        self._hook_map.clear()

    @property
    def hooks(self) -> List[BaseHook]:
        """Get all registered hooks (ordered by priority)."""
        return [hook for _, hook in self._hooks]
