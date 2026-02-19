"""
Base authentication and storage provider interfaces.

Provides pluggable authentication and multi-tenant storage management.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from cortex.core.storage.store import CortexStorage


class BaseAuthProvider(ABC):
    """
    Base authentication provider interface.

    Applications can implement this to provide custom auth logic.

    Examples:
        >>> class MyAuthProvider(BaseAuthProvider):
        ...     def authenticate(self, credentials):
        ...         # Custom validation logic
        ...         if credentials.get("api_key") == "valid":
        ...             return {"user_id": "123", "role": "admin"}
        ...         return None
    """

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Authenticate and return auth context.

        Args:
            credentials: Auth credentials (API key, token, etc.)

        Returns:
            Auth context dict (e.g., {"user_id": ..., "org_id": ...})
            None if authentication fails

        Raises:
            CortexAuthenticationError: If auth fails with details

        Examples:
            >>> provider = MyAuthProvider()
            >>> context = provider.authenticate({"api_key": "my-key"})
            >>> print(context["user_id"])
            '123'
        """
        pass


class BaseStorageProvider(ABC):
    """
    Base storage provider for multi-tenant scenarios.

    Handles setup/teardown of tenant-specific storage instances.
    Renamed from BaseContextProvider for clarity.

    Examples:
        >>> class MyStorageProvider(BaseStorageProvider):
        ...     def get_storage(self, auth_context):
        ...         tenant_id = auth_context["tenant_id"]
        ...         return self._get_cached_storage(tenant_id)
        ...
        ...     def cleanup_storage(self):
        ...         # Cleanup resources
        ...         pass
    """

    @abstractmethod
    def get_storage(self, auth_context: Dict[str, Any]) -> CortexStorage:
        """
        Get storage instance for authenticated context.

        For multi-tenant apps, this might:
        - Create tenant-specific CortexStorage
        - Configure database schema/connection per tenant
        - Set up file storage paths per tenant

        Args:
            auth_context: Authentication context from BaseAuthProvider

        Returns:
            CortexStorage instance for this tenant/user

        Examples:
            >>> provider = MyStorageProvider()
            >>> storage = provider.get_storage({"tenant_id": "org1"})
            >>> # storage is configured for org1's database schema
        """
        pass

    @abstractmethod
    def cleanup_storage(self) -> None:
        """
        Clean up storage resources.

        Should be called when switching tenants or on client close.

        Examples:
            >>> provider = MyStorageProvider()
            >>> provider.cleanup_storage()
        """
        pass

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup happens."""
        self.cleanup_storage()
