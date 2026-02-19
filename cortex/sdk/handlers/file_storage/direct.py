"""
Direct mode implementations for file storage operations.

Calls Core services directly for local file operations.
"""
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
import logging

from cortex.core.services.data.sources.files import FileStorageService
from cortex.core.exceptions.data.sources import FileDoesNotExistError, FileHasDependenciesError
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError

logger = logging.getLogger(__name__)


def upload_files(
    environment_id: UUID,
    files: List[Tuple[str, bytes]],
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Upload files - direct Core service call.

    Args:
        environment_id: Environment ID
        files: List of (filename, content) tuples
        overwrite: Whether to overwrite existing files

    Returns:
        Dictionary with uploaded file information

    Raises:
        CortexValidationError: If validation fails
    """
    try:
        service = FileStorageService()
        uploaded_files = service.upload_files(
            environment_id=environment_id,
            files=files,
            overwrite=overwrite
        )

        return {
            "file_ids": [str(f.id) for f in uploaded_files],
            "files": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "extension": f.extension,
                    "size": f.size,
                    "mime_type": f.mime_type,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in uploaded_files
            ],
            "message": f"Uploaded {len(uploaded_files)} file(s)"
        }
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_files(
    environment_id: UUID,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    List uploaded files - direct Core service call.

    Args:
        environment_id: Environment ID
        limit: Optional limit on number of files

    Returns:
        Dictionary with list of files
    """
    try:
        service = FileStorageService()
        files = service.list_files(
            environment_id=environment_id,
            limit=limit
        )

        return {
            "files": [
                {
                    "id": str(f.id),
                    "name": f.name,
                    "extension": f.extension,
                    "size": f.size,
                    "mime_type": f.mime_type,
                    "hash": f.hash,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                }
                for f in files
            ]
        }
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_file(
    file_id: UUID,
    environment_id: UUID,
    cascade: bool = False
) -> None:
    """
    Delete a file - direct Core service call.

    Args:
        file_id: File ID to delete
        environment_id: Environment ID
        cascade: If true, delete dependent data sources and metrics

    Raises:
        CortexNotFoundError: If file doesn't exist
        CortexValidationError: If file has dependencies and cascade=False
    """
    try:
        if not FileStorageService.delete_file(file_id, environment_id, cascade=cascade):
            raise CortexNotFoundError(f"File {file_id} not found")
    except FileDoesNotExistError as e:
        raise CortexNotFoundError(str(e))
    except FileHasDependenciesError as e:
        # Get dependencies for better error message
        dependencies = FileStorageService.get_file_dependencies(file_id)
        error_detail = {
            "error": "FileHasDependencies",
            "message": str(e),
            "file_id": str(file_id),
            "dependencies": dependencies
        }
        raise CoreExceptionMapper().map(e, details=error_detail)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
