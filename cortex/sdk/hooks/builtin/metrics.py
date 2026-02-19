"""
Metrics collection hook.

Collects timing and count metrics for operations.
"""
import time
from typing import Any, Dict

from cortex.sdk.events.types import HookEventType
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.contexts import EventContext, QueryEventContext


class MetricsHook(BaseHook):
    """
    Collect timing and count metrics for operations.

    Tracks operation counts and execution times. Useful for monitoring
    and performance analysis.

    Attributes:
        operation_counts: Count of each operation
        operation_timings: List of execution times per operation
        _start_times: Internal tracking of start times

    Examples:
        >>> from cortex.sdk import CortexClient
        >>> from cortex.sdk.hooks.builtin import MetricsHook
        >>>
        >>> metrics_hook = MetricsHook()
        >>> client = CortexClient(
        ...     mode="direct",
        ...     hooks=[metrics_hook]
        ... )
        >>>
        >>> # Perform operations...
        >>> metrics = client.metrics.list()
        >>>
        >>> # Get collected stats
        >>> stats = metrics_hook.get_stats()
        >>> print(stats)
        >>> # {'metrics.list': {'count': 1, 'avg_ms': 45.2, 'min_ms': 45.2, 'max_ms': 45.2}}
    """

    def __init__(self):
        """Initialize metrics collection hook."""
        super().__init__("MetricsHook")
        self.operation_counts: Dict[str, int] = {}
        self.operation_timings: Dict[str, list[float]] = {}
        self._start_times: Dict[int, float] = {}

    def handle(self, context: EventContext) -> EventContext:
        """
        Collect metrics for the operation.

        Args:
            context: Event context

        Returns:
            Context with timing data added (for query events)
        """
        operation_key = f"{context.manager}.{context.action}"

        if context.event_type == HookEventType.BEFORE:
            # Record start time using context object id
            self._start_times[id(context)] = time.time()

        elif context.event_type == HookEventType.AFTER:
            # Record completion
            self.operation_counts[operation_key] = (
                self.operation_counts.get(operation_key, 0) + 1
            )

            # Calculate duration if we have start time
            start_time = self._start_times.pop(id(context), None)
            if start_time:
                duration = (time.time() - start_time) * 1000  # ms
                if operation_key not in self.operation_timings:
                    self.operation_timings[operation_key] = []
                self.operation_timings[operation_key].append(duration)

                # Add to context for query events
                if isinstance(context, QueryEventContext):
                    context.duration_ms = duration

        elif context.event_type == HookEventType.ERROR:
            # Clean up start time on error
            self._start_times.pop(id(context), None)

        return context

    def get_stats(self) -> Dict[str, Any]:
        """
        Get collected metrics.

        Returns:
            Dict with operation stats (count, avg_ms, min_ms, max_ms)

        Examples:
            >>> hook = MetricsHook()
            >>> # ... perform operations ...
            >>> stats = hook.get_stats()
            >>> print(f"Operations: {len(stats)}")
        """
        stats = {}
        for operation, timings in self.operation_timings.items():
            if timings:
                stats[operation] = {
                    "count": self.operation_counts.get(operation, 0),
                    "avg_ms": sum(timings) / len(timings),
                    "min_ms": min(timings),
                    "max_ms": max(timings),
                }
        return stats

    def reset_stats(self) -> None:
        """
        Reset all collected metrics.

        Examples:
            >>> hook.reset_stats()
        """
        self.operation_counts.clear()
        self.operation_timings.clear()
        self._start_times.clear()
