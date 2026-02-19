"""
Base exception classes for Cortex SDK.

Provides a hierarchy of exceptions for different error scenarios.
"""
from typing import Any, Dict, Optional


class CortexSDKError(Exception):
    """
    Base exception for all SDK errors.

    All SDK exceptions inherit from this class, making it easy to catch
    any SDK-related error.

    Attributes:
        message: Error message
        details: Additional error details

    Examples:
        >>> try:
        ...     # SDK operation
        ...     pass
        ... except CortexSDKError as e:
        ...     print(f"SDK error: {e.message}")
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class CortexHTTPError(CortexSDKError):
    """
    HTTP-related errors (API mode).

    Raised when HTTP requests fail in API mode.

    Attributes:
        status_code: HTTP status code
        message: Error message
        details: Additional error details

    Examples:
        >>> raise CortexHTTPError(404, "Resource not found")
    """

    def __init__(self, status_code: int, message: str, details: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        super().__init__(message, details)


class CortexNotFoundError(CortexSDKError):
    """
    Resource not found error.

    Raised when a requested resource does not exist.

    Examples:
        >>> raise CortexNotFoundError("Metric with ID abc123 not found")
    """

    pass


class CortexValidationError(CortexSDKError):
    """
    Validation error.

    Raised when input validation fails.

    Examples:
        >>> raise CortexValidationError("Invalid metric configuration")
    """

    pass


class CortexAuthenticationError(CortexSDKError):
    """
    Authentication failed.

    Raised when authentication credentials are invalid or missing.

    Examples:
        >>> raise CortexAuthenticationError("Invalid API key")
    """

    pass


class CortexAuthorizationError(CortexSDKError):
    """
    Authorization failed.

    Raised when user lacks permission for an operation.

    Examples:
        >>> raise CortexAuthorizationError("Insufficient permissions")
    """

    pass


class CortexServerError(CortexSDKError):
    """
    Server error (5xx).

    Raised when the server encounters an internal error.

    Examples:
        >>> raise CortexServerError("Internal server error")
    """

    pass


class CortexConfigurationError(CortexSDKError):
    """
    Configuration error.

    Raised when SDK configuration is invalid.

    Examples:
        >>> raise CortexConfigurationError("API mode requires host parameter")
    """

    pass


class CortexConnectionError(CortexSDKError):
    """
    Connection error.

    Raised when unable to connect to the API server.

    Examples:
        >>> raise CortexConnectionError("Unable to connect to host")
    """

    pass


class CortexTimeoutError(CortexSDKError):
    """
    Timeout error.

    Raised when an operation exceeds the timeout limit.

    Examples:
        >>> raise CortexTimeoutError("Request timed out after 60s")
    """

    pass
