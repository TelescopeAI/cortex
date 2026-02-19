"""
API key authentication provider.

Function-based validation for maximum flexibility.
"""
from typing import Any, Callable, Dict, Optional

from cortex.sdk.auth.base import BaseAuthProvider
from cortex.sdk.exceptions import CortexAuthenticationError


class APIKeyAuthProvider(BaseAuthProvider):
    """
    API key authentication with custom validation function.

    Developers provide their own validation logic via a function.

    Attributes:
        validate_func: Function that takes API key and returns auth context

    Examples:
        Simple validation:
        >>> def my_validator(api_key: str) -> Optional[Dict[str, Any]]:
        ...     if api_key.startswith("valid_"):
        ...         return {"user_id": "123", "role": "admin"}
        ...     return None
        ...
        >>> auth_provider = APIKeyAuthProvider(validate_func=my_validator)
        >>> context = auth_provider.authenticate({"api_key": "valid_abc"})

        Database-backed validation:
        >>> def db_validator(api_key: str) -> Optional[Dict[str, Any]]:
        ...     user = db.query("SELECT * FROM api_keys WHERE key = ?", api_key)
        ...     if user:
        ...         return {"user_id": user.id, "role": user.role}
        ...     return None
        ...
        >>> auth_provider = APIKeyAuthProvider(validate_func=db_validator)

        Encrypted key validation (Humane pattern):
        >>> def encrypted_validator(api_key: str) -> Optional[Dict[str, Any]]:
        ...     # Decrypt and validate
        ...     decrypted = cipher.decrypt(api_key)
        ...     if is_valid(decrypted):
        ...         return {"org_id": "...", "user_id": "..."}
        ...     return None
    """

    def __init__(self, validate_func: Callable[[str], Optional[Dict[str, Any]]]):
        """
        Initialize with custom validation function.

        Args:
            validate_func: Function that takes API key and returns auth context
                          (or None if invalid)

        Examples:
            >>> def my_validator(api_key: str):
            ...     return {"user_id": "123"} if api_key == "valid" else None
            ...
            >>> provider = APIKeyAuthProvider(validate_func=my_validator)
        """
        self.validate_func = validate_func

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Authenticate using API key.

        Args:
            credentials: Dict containing "api_key"

        Returns:
            Auth context from validation function

        Raises:
            CortexAuthenticationError: If API key missing or invalid

        Examples:
            >>> provider = APIKeyAuthProvider(validate_func=my_validator)
            >>> context = provider.authenticate({"api_key": "my-key"})
            >>> print(context["user_id"])
            '123'
        """
        api_key = credentials.get("api_key")
        if not api_key:
            raise CortexAuthenticationError("API key required")

        # Call custom validation function
        context = self.validate_func(api_key)
        if not context:
            raise CortexAuthenticationError("Invalid API key")

        return context
