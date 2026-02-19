"""
Direct transport implementation for Direct mode.

Bypasses FastAPI and directly calls Core services for maximum performance.
"""
from typing import Any, Dict, Optional, Union
from pathlib import Path
from uuid import UUID
import io
import logging
import re

from cortex.sdk.transport.base import BaseTransport
from cortex.sdk.auth.base import BaseStorageProvider
from cortex.sdk.hooks.manager import HookManager
from cortex.sdk.exceptions.mappers import CortexExceptionMapper
from cortex.sdk.exceptions.base import (
    CortexNotFoundError,
    CortexValidationError,
)

# Core imports
from cortex.core.storage.database import LocalSession

logger = logging.getLogger(__name__)


class DirectTransport(BaseTransport):
    """
    Direct transport for Direct mode.

    Bypasses FastAPI and directly calls Core services for maximum performance.
    Handles database session management and exception mapping.

    Attributes:
        storage: Optional custom storage instance
        storage_provider: Optional storage provider for multi-tenancy
        hooks: Hook manager

    Examples:
        Basic usage:
        >>> transport = DirectTransport()
        >>> result = transport.get("/metrics", params={"environment_id": env_id})

        With custom storage:
        >>> storage = CortexStorage(...)
        >>> transport = DirectTransport(storage=storage)

        With storage provider (multi-tenant):
        >>> provider = MyStorageProvider()
        >>> transport = DirectTransport(storage_provider=provider)
    """

    def __init__(
        self,
        storage: Optional[Any] = None,
        storage_provider: Optional[BaseStorageProvider] = None,
        hooks: Optional[HookManager] = None,
    ):
        """
        Initialize Direct transport.

        Args:
            storage: Optional custom storage instance
            storage_provider: Optional storage provider for multi-tenancy
            hooks: Hook manager for event emission
        """
        super().__init__(hooks=hooks)
        self.storage = storage
        self.storage_provider = storage_provider
        self._session = None
        self._exception_mapper = CortexExceptionMapper()

    def _get_session(self):
        """
        Get database session.

        Returns:
            Database session
        """
        if self._session is None:
            if self.storage:
                # Use custom storage
                self._session = self.storage.get_session()
            else:
                # Use default LocalSession
                self._session = LocalSession().get_session()
        return self._session

    def _close_session(self):
        """Close and clean up database session."""
        if self._session:
            try:
                self._session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")
            finally:
                self._session = None

    def _parse_endpoint(
        self, endpoint: str
    ) -> tuple[str, Optional[str], Optional[str]]:
        """
        Parse endpoint to extract resource type, ID, and action.

        Args:
            endpoint: API endpoint

        Returns:
            Tuple of (resource_type, resource_id, action)

        Examples:
            "/metrics" → ("metrics", None, None)
            "/metrics/123" → ("metrics", "123", None)
            "/metrics/123/execute" → ("metrics", "123", "execute")
            "/data/sources" → ("data_sources", None, None)
            "/data/sources/files/123/download" → ("files", "123", "download")
        """
        endpoint = endpoint.strip("/")
        parts = endpoint.split("/")

        # Handle nested resources (e.g., /data/sources, /data/models)
        if parts[0] == "data":
            if len(parts) >= 2:
                resource_type = f"data_{parts[1]}"  # data_sources, data_models
                if len(parts) >= 3:
                    resource_id = parts[2]
                    action = parts[3] if len(parts) >= 4 else None
                else:
                    resource_id = None
                    action = None
            else:
                resource_type = "data"
                resource_id = None
                action = None
        else:
            resource_type = parts[0]
            resource_id = parts[1] if len(parts) >= 2 else None
            action = parts[2] if len(parts) >= 3 else None

        return resource_type, resource_id, action

    def _route_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None
    ) -> Any:
        """
        Route request to appropriate Core service.

        Args:
            method: HTTP method (get, post, put, patch, delete)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Service response

        Raises:
            CortexSDKError: On service call failure
        """
        resource_type, resource_id, action = self._parse_endpoint(endpoint)

        logger.debug(
            f"Direct {method.upper()} {endpoint} -> {resource_type}/{resource_id}/{action}"
        )

        # Route to appropriate handler
        if resource_type == "metrics":
            return self._handle_metrics(method, resource_id, action, params, data)
        elif resource_type == "metric_variants" or (resource_type == "metrics" and "variants" in endpoint):
            return self._handle_metric_variants(method, resource_id, action, params, data)
        elif resource_type == "data_sources":
            return self._handle_data_sources(method, resource_id, action, params, data)
        elif resource_type == "data_models":
            return self._handle_data_models(method, resource_id, action, params, data)
        elif resource_type == "dashboards":
            return self._handle_dashboards(method, resource_id, action, params, data)
        elif resource_type == "workspaces":
            return self._handle_workspaces(method, resource_id, action, params, data)
        elif resource_type == "environments":
            return self._handle_environments(method, resource_id, action, params, data)
        elif resource_type == "files" or (resource_type == "data_sources" and "files" in endpoint):
            return self._handle_files(method, resource_id, action, params, data)
        else:
            raise CortexValidationError(f"Unknown resource type: {resource_type}")

    def _handle_metrics(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """
        Handle metrics operations.

        This is a placeholder that will be fully implemented when we have access
        to the MetricService import.
        """
        from cortex.core.data.db.metric_service import MetricService

        service = MetricService()

        try:
            if method == "get":
                if resource_id is None:
                    # List metrics
                    environment_id = params.get("environment_id") if params else None
                    if not environment_id:
                        raise CortexValidationError("environment_id required")

                    metrics = service.get_all_metrics(environment_id=UUID(environment_id))
                    return {"metrics": [m.model_dump() for m in metrics]}
                else:
                    # Get single metric
                    environment_id = params.get("environment_id") if params else None
                    metric = service.get_metric_by_id(
                        metric_id=UUID(resource_id),
                        environment_id=UUID(environment_id) if environment_id else None
                    )
                    if not metric:
                        raise CortexNotFoundError(f"Metric not found: {resource_id}")
                    return metric.model_dump()

            elif method == "post":
                # Create metric
                if not data:
                    raise CortexValidationError("Request data required")

                metric = service.create_metric(**data)
                return metric.model_dump()

            elif method == "put" or method == "patch":
                # Update metric
                if not resource_id:
                    raise CortexValidationError("Metric ID required")
                if not data:
                    raise CortexValidationError("Update data required")

                environment_id = data.get("environment_id")
                metric = service.update_metric(
                    metric_id=UUID(resource_id),
                    environment_id=UUID(environment_id) if environment_id else None,
                    **data
                )
                return metric.model_dump()

            elif method == "delete":
                # Delete metric
                if not resource_id:
                    raise CortexValidationError("Metric ID required")

                environment_id = params.get("environment_id") if params else None
                service.delete_metric(
                    metric_id=UUID(resource_id),
                    environment_id=UUID(environment_id) if environment_id else None
                )
                return None

            else:
                raise CortexValidationError(f"Unsupported method: {method}")

        except Exception as e:
            # Map Core exceptions to SDK exceptions
            raise self._exception_mapper.map_exception(e)
        finally:
            service.close()

    def _handle_metric_variants(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle metric variants operations (placeholder)."""
        raise NotImplementedError("Metric variants not yet implemented in Direct transport")

    def _handle_data_sources(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle data sources operations (placeholder)."""
        raise NotImplementedError("Data sources not yet implemented in Direct transport")

    def _handle_data_models(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle data models operations (placeholder)."""
        raise NotImplementedError("Data models not yet implemented in Direct transport")

    def _handle_dashboards(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle dashboards operations (placeholder)."""
        raise NotImplementedError("Dashboards not yet implemented in Direct transport")

    def _handle_workspaces(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle workspaces operations (placeholder)."""
        raise NotImplementedError("Workspaces not yet implemented in Direct transport")

    def _handle_environments(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle environments operations (placeholder)."""
        raise NotImplementedError("Environments not yet implemented in Direct transport")

    def _handle_files(
        self, method: str, resource_id: Optional[str], action: Optional[str],
        params: Optional[Dict], data: Optional[Dict]
    ) -> Any:
        """Handle file operations (placeholder)."""
        raise NotImplementedError("Files not yet implemented in Direct transport")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute GET request via Direct Core access."""
        return self._route_request("get", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute POST request via Direct Core access."""
        return self._route_request("post", endpoint, data=data)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute PUT request via Direct Core access."""
        return self._route_request("put", endpoint, data=data)

    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute PATCH request via Direct Core access."""
        return self._route_request("patch", endpoint, data=data)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Execute DELETE request via Direct Core access."""
        return self._route_request("delete", endpoint, params=params)

    def upload_file(
        self,
        endpoint: str,
        file: Union[Path, str, bytes, io.IOBase],
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Upload file via Direct Core access.

        Placeholder - will be implemented with file storage service.
        """
        raise NotImplementedError("File upload not yet implemented in Direct transport")

    def download_file(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bytes:
        """
        Download file via Direct Core access.

        Placeholder - will be implemented with file storage service.
        """
        raise NotImplementedError("File download not yet implemented in Direct transport")

    def close(self) -> None:
        """Close database session."""
        self._close_session()
