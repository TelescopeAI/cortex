"""
Base transport interface for SDK operations.

Defines abstract interface for both HTTP (API mode) and Direct (Core mode) transports.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from pathlib import Path
import io

from cortex.sdk.hooks.manager import HookManager


class BaseTransport(ABC):
    """
    Abstract base class for transport implementations.

    Transport handles communication between SDK managers and backend (API or Core).
    Implementations must handle HTTP requests (API mode) or direct Core calls (Direct mode).

    Attributes:
        hooks: Optional hook manager for event emission

    Examples:
        HTTP Transport (API mode):
        >>> transport = HTTPTransport(
        ...     host="http://localhost:9002/api/v1",
        ...     auth_provider=api_key_provider
        ... )
        >>> result = transport.get("/metrics", params={"environment_id": env_id})

        Direct Transport (Direct mode):
        >>> transport = DirectTransport()
        >>> result = transport.get("/metrics", params={"environment_id": env_id})
    """

    def __init__(self, hooks: Optional[HookManager] = None):
        """
        Initialize transport.

        Args:
            hooks: Optional hook manager for event emission
        """
        self._hooks = hooks

    @abstractmethod
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute GET request.

        Args:
            endpoint: API endpoint (e.g., "/metrics")
            params: Query parameters
            **kwargs: Additional transport-specific parameters

        Returns:
            Response data (dict or Pydantic model)

        Raises:
            CortexSDKError: On request failure

        Examples:
            >>> result = transport.get("/metrics", params={"environment_id": env_id})
            >>> metric = transport.get(f"/metrics/{metric_id}")
        """
        pass

    @abstractmethod
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute POST request.

        Args:
            endpoint: API endpoint (e.g., "/metrics")
            data: Request body data
            **kwargs: Additional transport-specific parameters

        Returns:
            Response data (dict or Pydantic model)

        Raises:
            CortexSDKError: On request failure

        Examples:
            >>> metric = transport.post("/metrics", data=metric_config)
        """
        pass

    @abstractmethod
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute PUT request.

        Args:
            endpoint: API endpoint (e.g., "/metrics/{id}")
            data: Request body data
            **kwargs: Additional transport-specific parameters

        Returns:
            Response data (dict or Pydantic model)

        Raises:
            CortexSDKError: On request failure

        Examples:
            >>> metric = transport.put(f"/metrics/{metric_id}", data=updates)
        """
        pass

    @abstractmethod
    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute PATCH request.

        Args:
            endpoint: API endpoint (e.g., "/metrics/{id}")
            data: Partial update data
            **kwargs: Additional transport-specific parameters

        Returns:
            Response data (dict or Pydantic model)

        Raises:
            CortexSDKError: On request failure

        Examples:
            >>> metric = transport.patch(f"/metrics/{metric_id}", data={"name": "New Name"})
        """
        pass

    @abstractmethod
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute DELETE request.

        Args:
            endpoint: API endpoint (e.g., "/metrics/{id}")
            params: Query parameters (e.g., cascade=true)
            **kwargs: Additional transport-specific parameters

        Returns:
            Response data (dict or None)

        Raises:
            CortexSDKError: On request failure

        Examples:
            >>> transport.delete(f"/metrics/{metric_id}")
            >>> transport.delete(f"/data/sources/{source_id}", params={"cascade": True})
        """
        pass

    @abstractmethod
    def upload_file(
        self,
        endpoint: str,
        file: Union[Path, str, bytes, io.IOBase],
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Upload file.

        Args:
            endpoint: API endpoint (e.g., "/data/sources/files")
            file: File to upload (path, bytes, or file-like object)
            filename: Optional filename override
            params: Additional parameters
            **kwargs: Additional transport-specific parameters

        Returns:
            File metadata response

        Raises:
            CortexSDKError: On upload failure

        Examples:
            >>> metadata = transport.upload_file(
            ...     "/data/sources/files",
            ...     file="data.csv",
            ...     params={"workspace_id": ws_id}
            ... )
        """
        pass

    @abstractmethod
    def download_file(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bytes:
        """
        Download file.

        Args:
            endpoint: API endpoint (e.g., "/data/sources/files/{id}/download")
            params: Query parameters
            **kwargs: Additional transport-specific parameters

        Returns:
            File content as bytes

        Raises:
            CortexSDKError: On download failure

        Examples:
            >>> content = transport.download_file(f"/data/sources/files/{file_id}/download")
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Clean up transport resources.

        Called when transport is no longer needed. Implementations should:
        - Close HTTP connections
        - Release database sessions
        - Clean up any other resources

        Examples:
            >>> transport.close()
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - auto-cleanup."""
        self.close()
