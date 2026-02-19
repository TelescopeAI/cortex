"""
Session management for transport lifecycle.

Provides context manager support for automatic resource cleanup.
"""
from typing import Optional
import logging

from cortex.sdk.transport.base import BaseTransport

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session manager for transport lifecycle.

    Provides context manager support for automatic cleanup of transport resources.
    Useful for ensuring proper session management and resource cleanup.

    Attributes:
        transport: Transport instance to manage

    Examples:
        Basic usage:
        >>> transport = DirectTransport()
        >>> with SessionManager(transport) as session:
        ...     result = session.get("/metrics")
        # Auto-cleanup happens here

        Manual management:
        >>> manager = SessionManager(transport)
        >>> try:
        ...     result = manager.transport.get("/metrics")
        ... finally:
        ...     manager.close()
    """

    def __init__(self, transport: BaseTransport):
        """
        Initialize session manager.

        Args:
            transport: Transport instance to manage
        """
        self.transport = transport
        self._is_closed = False

    def __enter__(self):
        """
        Context manager entry.

        Returns:
            Transport instance
        """
        return self.transport

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - auto cleanup.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)
        """
        self.close()

        # Don't suppress exceptions
        return False

    def close(self):
        """
        Close transport and clean up resources.

        Safe to call multiple times.
        """
        if not self._is_closed:
            try:
                self.transport.close()
            except Exception as e:
                logger.error(f"Error closing transport: {e}", exc_info=True)
            finally:
                self._is_closed = True

    def __del__(self):
        """Destructor - ensure cleanup."""
        self.close()
