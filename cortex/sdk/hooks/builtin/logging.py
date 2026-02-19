"""
Logging hook for debugging and auditing.

Logs all SDK operations using Python's logging module.
"""
import logging
from typing import Optional

from cortex.sdk.events.types import HookEventType
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.contexts import EventContext


class LoggingHook(BaseHook):
    """
    Log all SDK operations.

    Useful for debugging and auditing. Logs operation start, completion,
    and errors using Python's logging module.

    Attributes:
        logger: Python logger instance
        level: Log level to use

    Examples:
        Basic usage:
        >>> from cortex.sdk import CortexClient
        >>> from cortex.sdk.hooks.builtin import LoggingHook
        >>>
        >>> client = CortexClient(
        ...     mode="direct",
        ...     hooks=[LoggingHook()]
        ... )

        Custom logger and level:
        >>> import logging
        >>> my_logger = logging.getLogger("my_app.cortex")
        >>> hook = LoggingHook(logger=my_logger, level=logging.DEBUG)
    """

    def __init__(
        self, logger: Optional[logging.Logger] = None, level: int = logging.INFO
    ):
        """
        Initialize logging hook.

        Args:
            logger: Python logger (defaults to cortex.sdk logger)
            level: Log level (default: INFO)

        Examples:
            >>> hook = LoggingHook()
            >>> hook = LoggingHook(level=logging.DEBUG)
        """
        super().__init__("LoggingHook")
        self.logger = logger or logging.getLogger("cortex.sdk")
        self.level = level

    def handle(self, context: EventContext) -> EventContext:
        """
        Log the operation.

        Args:
            context: Event context

        Returns:
            Unmodified context

        Examples:
            >>> # Logs output like:
            >>> # [metrics.create] Starting...
            >>> # [metrics.create] Completed
        """
        if context.event_type == HookEventType.BEFORE:
            self.logger.log(self.level, f"[{context.operation}] Starting...")

        elif context.event_type == HookEventType.AFTER:
            self.logger.log(self.level, f"[{context.operation}] Completed")

        elif context.event_type == HookEventType.ERROR:
            self.logger.error(
                f"[{context.operation}] Failed: {context.error}", exc_info=True
            )

        return context
