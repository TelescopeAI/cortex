"""
HTTP client for API mode operations.

Provides HTTP communication with retry logic and error handling.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
import io
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from cortex.sdk.auth.base import BaseAuthProvider
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


class CortexHTTPClient:
    """
    HTTP client for Cortex API mode operations.

    Handles HTTP requests with automatic retry, error mapping, and authentication.

    Attributes:
        host: API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Examples:
        >>> client = CortexHTTPClient(host="http://localhost:9002/api/v1")
        >>> response = client.get("/metrics", params={"environment_id": env_id})
    """

    def __init__(
        self,
        host: str,
        auth_provider: Optional[BaseAuthProvider] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize HTTP client.

        Args:
            host: API base URL (e.g., "http://localhost:9002/api/v1")
            auth_provider: Optional authentication provider
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.host = host.rstrip("/")
        self.auth_provider = auth_provider
        self.timeout = timeout
        self.max_retries = max_retries

        # Create httpx client
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}

        if self.auth_provider:
            auth_headers = self.auth_provider.get_headers()
            headers.update(auth_headers)

        return headers

    def _handle_error(self, response: httpx.Response) -> None:
        """
        Map HTTP status codes to SDK exceptions.

        Args:
            response: HTTP response

        Raises:
            CortexAuthenticationError: 401 Unauthorized
            CortexAuthorizationError: 403 Forbidden
            CortexNotFoundError: 404 Not Found
            CortexValidationError: 422 Unprocessable Entity
            CortexServerError: 5xx Server Error
        """
        status = response.status_code

        try:
            error_data = response.json()
            detail = error_data.get("detail", response.text)
        except Exception:
            detail = response.text

        if status == 401:
            raise CortexAuthenticationError(f"Authentication failed: {detail}")
        elif status == 403:
            raise CortexAuthorizationError(f"Authorization failed: {detail}")
        elif status == 404:
            raise CortexNotFoundError(f"Resource not found: {detail}")
        elif status == 422:
            raise CortexValidationError(f"Validation error: {detail}")
        elif 500 <= status < 600:
            raise CortexServerError(f"Server error ({status}): {detail}")
        else:
            raise CortexServerError(f"HTTP error ({status}): {detail}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON request body
            data: Form data
            files: Multipart files

        Returns:
            HTTP response

        Raises:
            CortexTimeoutError: Request timeout
            CortexConnectionError: Connection error
        """
        url = f"{self.host}{endpoint}"
        headers = self._get_headers()

        # Remove Content-Type for multipart requests
        if files:
            headers.pop("Content-Type", None)

        try:
            logger.debug(f"{method} {url}")
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                self._handle_error(response)

            return response

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {url}")
            raise CortexTimeoutError(f"Request timeout: {str(e)}") from e
        except (httpx.ConnectError, httpx.NetworkError) as e:
            logger.error(f"Connection error: {url}")
            raise CortexConnectionError(f"Connection error: {str(e)}") from e

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.get("/metrics", params={"environment_id": env_id})
        """
        response = self._request("GET", endpoint, params=params)
        return response.json()

    def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.post("/metrics", data={"name": "Revenue"})
        """
        response = self._request("POST", endpoint, json=data)
        return response.json()

    def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.put("/metrics/123", data={"name": "Updated"})
        """
        response = self._request("PUT", endpoint, json=data)
        return response.json()

    def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PATCH request.

        Args:
            endpoint: API endpoint path
            data: Request body

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.patch("/metrics/123", data={"name": "Patched"})
        """
        response = self._request("PATCH", endpoint, json=data)
        return response.json()

    def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.delete("/metrics/123")
        """
        response = self._request("DELETE", endpoint, params=params)

        # Handle empty responses
        if not response.content:
            return {"success": True}

        return response.json()

    def upload_file(
        self,
        endpoint: str,
        file: Union[Path, str, bytes, io.IOBase],
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload file with multipart/form-data encoding.

        Args:
            endpoint: API endpoint path
            file: File to upload (path, bytes, or file-like object)
            filename: Optional filename override
            params: Query parameters

        Returns:
            JSON response as dict

        Examples:
            >>> response = client.upload_file("/files", "data.csv")
            >>> response = client.upload_file("/files", file_bytes, filename="data.csv")
        """
        # Prepare file for upload
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            file_name = filename or file_path.name
            with open(file_path, "rb") as f:
                file_content = f.read()
        elif isinstance(file, bytes):
            file_name = filename or "upload"
            file_content = file
        elif hasattr(file, "read"):
            file_name = filename or "upload"
            file_content = file.read()
        else:
            raise ValueError("Invalid file type")

        files = {"file": (file_name, file_content)}
        response = self._request("POST", endpoint, params=params, files=files)
        return response.json()

    def download_file(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Download file content.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            File content as bytes

        Examples:
            >>> content = client.download_file("/files/123/download")
            >>> with open("output.csv", "wb") as f:
            ...     f.write(content)
        """
        response = self._request("GET", endpoint, params=params)
        return response.content

    def close(self):
        """Close HTTP client and release resources."""
        self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit - auto cleanup."""
        self.close()
