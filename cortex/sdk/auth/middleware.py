"""
Request/response middleware for SDK operations.

Provides interceptor pattern for cross-cutting concerns.
"""
from abc import ABC
from typing import Any, Dict


class RequestInterceptor(ABC):
    """
    Middleware pattern for pre/post request processing.

    Allows apps to inject custom logic around SDK operations.

    Examples:
        >>> class LoggingInterceptor(RequestInterceptor):
        ...     def before_request(self, operation, params):
        ...         print(f"Starting: {operation}")
        ...
        ...     def after_request(self, operation, result):
        ...         print(f"Completed: {operation}")
        ...         return result
    """

    def before_request(self, operation: str, params: Dict[str, Any]) -> None:
        """
        Called before SDK operation executes.

        Args:
            operation: Operation name (e.g., "metrics.create")
            params: Operation parameters

        Examples:
            >>> interceptor = MyInterceptor()
            >>> interceptor.before_request("metrics.create", {"name": "Revenue"})
        """
        pass

    def after_request(self, operation: str, result: Any) -> Any:
        """
        Called after SDK operation succeeds.

        Args:
            operation: Operation name
            result: Operation result

        Returns:
            Modified result (or original)

        Examples:
            >>> interceptor = MyInterceptor()
            >>> result = interceptor.after_request("metrics.create", metric)
        """
        return result

    def on_error(self, operation: str, error: Exception) -> None:
        """
        Called when SDK operation fails.

        Args:
            operation: Operation name
            error: Exception that occurred

        Examples:
            >>> interceptor = MyInterceptor()
            >>> interceptor.on_error("metrics.create", exc)
        """
        pass
