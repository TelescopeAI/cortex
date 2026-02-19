"""
HTTP transport implementation for API mode.

Uses httpx library for making HTTP requests to the Cortex API.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import io
import logging

try:
    import httpx
except ImportError:
    raise ImportError(
        "httpx is required for HTTP transport. Install with: pip install httpx"
    )

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from cortex.sdk.transport.base import BaseTransport
from cortex.sdk.auth.base import BaseAuthProvider
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.exceptions.base import (
    CortexAuthenticationError,
    CortexAuthorizationError,
    CortexNotFoundError,
    CortexValidationError,
    CortexServerError,
    CortexConnectionError,
    CortexTimeoutError,
)

logger = logging.getLogger(__name__)


class HTTPTransport(BaseTransport):
    """
    HTTP transport for API mode.

    Makes HTTP requests to Cortex API using httpx library.

    Attributes:
        host: API base URL
        auth_provider: Authentication provider
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        hooks: Hook manager

    Examples:
        Basic usage:
        >>> transport = HTTPTransport(host="http://localhost:9002/api/v1")
        >>> result = transport.get("/metrics")

        With authentication:
        >>> auth = APIKeyAuthProvider(validate_func=my_validator)
        >>> transport = HTTPTransport(
        ...     host="http://localhost:9002/api/v1",
        ...     auth_provider=auth
        ... )

        With retries:
        >>> transport = HTTPTransport(
        ...     host="http://localhost:9002/api/v1",
        ...     timeout=60,
        ...     max_retries=5
        ... )
    """

    def __init__(
        self,
        host: str,
        auth_provider: Optional[BaseAuthProvider] = None,
        timeout: int = 30,
        max_retries: int = 3,
        hooks: Optional[HookManager] = None,
    ):
        """
        Initialize HTTP transport.

        Args:
            host: API base URL (e.g., "http://localhost:9002/api/v1")
            auth_provider: Authentication provider
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            hooks: Hook manager for event emission
        """
        super().__init__(hooks=hooks)
        self.host = host.rstrip("/")
        self.auth_provider = auth_provider
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from host and endpoint.

        Args:
            endpoint: API endpoint

        Returns:
            Full URL
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.host}/{endpoint}"

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers including authentication.

        Returns:
            Headers dict
        """
        headers = {"Content-Type": "application/json"}

        if self.auth_provider:
            auth_headers = self.auth_provider.get_headers()
            headers.update(auth_headers)

        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Handle HTTP error responses.

        Args:
            response: HTTP response

        Raises:
            CortexSDKError: Appropriate exception based on status code
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            message = error_data.get("detail", response.text)
        except Exception:
            message = response.text

        if status_code == 401:
            raise CortexAuthenticationError(message)
        elif status_code == 403:
            raise CortexAuthorizationError(message)
        elif status_code == 404:
            raise CortexNotFoundError(message)
        elif status_code == 422:
            raise CortexValidationError(message)
        elif status_code >= 500:
            raise CortexServerError(f"Server error ({status_code}): {message}")
        else:
            raise CortexServerError(f"HTTP error ({status_code}): {message}")

    def _make_request_with_retry(self, method: str, *args, **kwargs) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (get, post, put, patch, delete)
            *args: Request arguments
            **kwargs: Request keyword arguments

        Returns:
            HTTP response

        Raises:
            CortexConnectionError: On connection failure
            CortexTimeoutError: On timeout
        """

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(
                (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout)
            ),
        )
        def _request():
            try:
                request_method = getattr(self._client, method)
                return request_method(*args, **kwargs)
            except httpx.ConnectError as e:
                raise CortexConnectionError(f"Connection failed: {e}")
            except httpx.TimeoutException as e:
                raise CortexTimeoutError(f"Request timeout: {e}")

        return _request()

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional parameters

        Returns:
            Response data

        Raises:
            CortexSDKError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"GET {url} params={params}")

        response = self._make_request_with_retry(
            "get", url, params=params, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        return response.json()

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute POST request.

        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional parameters

        Returns:
            Response data

        Raises:
            CortexSDKError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"POST {url} data={data}")

        response = self._make_request_with_retry(
            "post", url, json=data, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        return response.json()

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute PUT request.

        Args:
            endpoint: API endpoint
            data: Request body data
            **kwargs: Additional parameters

        Returns:
            Response data

        Raises:
            CortexSDKError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"PUT {url} data={data}")

        response = self._make_request_with_retry(
            "put", url, json=data, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        return response.json()

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute PATCH request.

        Args:
            endpoint: API endpoint
            data: Partial update data
            **kwargs: Additional parameters

        Returns:
            Response data

        Raises:
            CortexSDKError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"PATCH {url} data={data}")

        response = self._make_request_with_retry(
            "patch", url, json=data, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        return response.json()

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute DELETE request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional parameters

        Returns:
            Response data or None

        Raises:
            CortexSDKError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"DELETE {url} params={params}")

        response = self._make_request_with_retry(
            "delete", url, params=params, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        # DELETE may return 204 No Content
        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception:
            return None

    def upload_file(
        self,
        endpoint: str,
        file: Union[Path, str, bytes, io.IOBase],
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Upload file using multipart/form-data.

        Args:
            endpoint: API endpoint
            file: File to upload
            filename: Optional filename override
            params: Additional parameters
            **kwargs: Additional parameters

        Returns:
            File metadata response

        Raises:
            CortexSDKError: On upload failure
        """
        url = self._build_url(endpoint)

        # Get auth headers (not Content-Type - httpx will set for multipart)
        headers = {}
        if self.auth_provider:
            auth_headers = self.auth_provider.get_headers()
            headers.update(auth_headers)

        # Prepare file
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            filename = filename or file_path.name
            file_content = open(file_path, "rb")
        elif isinstance(file, bytes):
            filename = filename or "file"
            file_content = io.BytesIO(file)
        else:
            file_content = file
            filename = filename or "file"

        logger.debug(f"POST {url} (file upload) filename={filename}")

        try:
            files = {"file": (filename, file_content)}
            response = self._make_request_with_retry(
                "post", url, files=files, params=params, headers=headers
            )

            if response.status_code >= 400:
                self._handle_error(response)

            return response.json()
        finally:
            if isinstance(file, (str, Path)):
                file_content.close()

    def download_file(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bytes:
        """
        Download file.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **kwargs: Additional parameters

        Returns:
            File content as bytes

        Raises:
            CortexSDKError: On download failure
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()

        logger.debug(f"GET {url} (file download) params={params}")

        response = self._make_request_with_retry(
            "get", url, params=params, headers=headers
        )

        if response.status_code >= 400:
            self._handle_error(response)

        return response.content

    def close(self) -> None:
        """Close HTTP client."""
        self._client.close()
