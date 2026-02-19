"""
File storage manager for file operations.

Handles file uploads, downloads, deletion, and management.
"""
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pathlib import Path
import io
import logging

from cortex.sdk.managers.base import BaseManager
from cortex.sdk.hooks.contexts import FileStorageEventContext
from cortex.sdk.events.types import CortexEvents
from cortex.sdk.exceptions.base import CortexValidationError

logger = logging.getLogger(__name__)


class FileStorageManager(BaseManager):
    """
    Manager for file storage operations.

    Handles:
    - File uploads (CSV, Excel, etc.)
    - File downloads
    - File deletion (with cascade support)
    - File listing and metadata retrieval
    - Spreadsheet preview

    Integrates with hooks system for file operation tracking and custom behavior.

    Examples:
        Upload file:
        >>> with open("data.csv", "rb") as f:
        ...     metadata = client.file_storage.upload(f, "data.csv")

        Download file:
        >>> content = client.file_storage.download(file_id)
        >>> with open("downloaded.csv", "wb") as f:
        ...     f.write(content)

        Delete file (cascade):
        >>> client.file_storage.delete(file_id, cascade=True)
    """

    def upload(
        self,
        file: Union[Path, str, bytes, io.IOBase],
        filename: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        environment_id: Optional[UUID] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Upload file.

        Args:
            file: File to upload (path, bytes, or file-like object)
            filename: Optional filename override
            workspace_id: Optional workspace ID (uses client context if not provided)
            environment_id: Optional environment ID (uses client context if not provided)
            **kwargs: Additional parameters

        Returns:
            File metadata

        Raises:
            CortexValidationError: If validation fails

        Examples:
            >>> metadata = client.file_storage.upload("data.csv")
            >>> metadata = client.file_storage.upload(file_bytes, filename="data.csv")
        """
        ws_id = workspace_id or self.workspace_id
        env_id = environment_id or self.environment_id

        params = {}
        if ws_id:
            params["workspace_id"] = str(ws_id)
        if env_id:
            params["environment_id"] = str(env_id)

        return self._execute_with_hooks(
            operation="file_storage.upload",
            event_name=CortexEvents.FILE_UPLOADED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.upload_file(
                "/data/sources/files", file=file, filename=filename, params=params
            ),
            workspace_id=ws_id,
            environment_id=env_id,
            filename=filename,
        )

    def download(self, file_id: UUID) -> bytes:
        """
        Download file content.

        Args:
            file_id: File ID

        Returns:
            File content as bytes

        Raises:
            CortexNotFoundError: If file doesn't exist

        Examples:
            >>> content = client.file_storage.download(file_id)
            >>> with open("output.csv", "wb") as f:
            ...     f.write(content)
        """
        return self._execute_with_hooks(
            operation="file_storage.download",
            event_name=CortexEvents.FILE_DOWNLOADED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.download_file(
                f"/data/sources/files/{file_id}/download"
            ),
            file_id=file_id,
        )

    def delete(self, file_id: UUID, cascade: bool = False) -> None:
        """
        Delete file.

        Args:
            file_id: File ID
            cascade: If True, delete dependent data sources and metrics

        Raises:
            CortexNotFoundError: If file doesn't exist
            CortexValidationError: If file has dependencies and cascade=False

        Examples:
            >>> client.file_storage.delete(file_id)
            >>> client.file_storage.delete(file_id, cascade=True)  # Delete with dependencies
        """
        self._execute_with_hooks(
            operation="file_storage.delete",
            event_name=CortexEvents.FILE_DELETED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.delete(
                f"/data/sources/files/{file_id}", params={"cascade": cascade}
            ),
            file_id=file_id,
        )

    def list(
        self,
        workspace_id: Optional[UUID] = None,
        environment_id: Optional[UUID] = None,
        **filters,
    ) -> Dict[str, Any]:
        """
        List files.

        Args:
            workspace_id: Optional workspace ID filter
            environment_id: Optional environment ID filter
            **filters: Additional filters (limit, offset, etc.)

        Returns:
            Paginated list of files

        Examples:
            >>> files = client.file_storage.list()
            >>> files = client.file_storage.list(workspace_id=ws_id)
            >>> files = client.file_storage.list(limit=10)
        """
        ws_id = workspace_id or self.workspace_id
        env_id = environment_id or self.environment_id

        params = {**filters}
        if ws_id:
            params["workspace_id"] = str(ws_id)
        if env_id:
            params["environment_id"] = str(env_id)

        return self._execute_with_hooks(
            operation="file_storage.list",
            event_name=CortexEvents.FILE_LISTED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.get("/data/sources/files", params=params),
            workspace_id=ws_id,
            environment_id=env_id,
        )

    def get(self, file_id: UUID) -> Dict[str, Any]:
        """
        Get file metadata.

        Args:
            file_id: File ID

        Returns:
            File metadata

        Raises:
            CortexNotFoundError: If file doesn't exist

        Examples:
            >>> metadata = client.file_storage.get(file_id)
            >>> print(f"File: {metadata['filename']}, Size: {metadata['file_size']}")
        """
        return self._execute_with_hooks(
            operation="file_storage.get",
            event_name=CortexEvents.FILE_RETRIEVED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.get(f"/data/sources/files/{file_id}"),
            file_id=file_id,
        )

    def preview_spreadsheet(
        self, file_id: UUID, sheet_name: Optional[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Preview spreadsheet data.

        Args:
            file_id: File ID
            sheet_name: Optional sheet name (for multi-sheet files)
            limit: Number of rows to preview

        Returns:
            Preview data with columns and rows

        Raises:
            CortexNotFoundError: If file doesn't exist
            CortexValidationError: If file is not a spreadsheet

        Examples:
            >>> preview = client.file_storage.preview_spreadsheet(file_id)
            >>> print(preview["columns"])
            >>> print(preview["rows"][:5])  # First 5 rows
        """
        params = {"limit": limit}
        if sheet_name:
            params["sheet_name"] = sheet_name

        return self._execute_with_hooks(
            operation="file_storage.preview_spreadsheet",
            event_name=CortexEvents.SPREADSHEET_SHEET_PREVIEWED,
            event_context_class=FileStorageEventContext,
            func=lambda: self._transport.get(
                f"/data/sources/files/{file_id}/preview", params=params
            ),
            file_id=file_id,
            filename=sheet_name,
        )
