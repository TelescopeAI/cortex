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
from cortex.sdk.exceptions.base import CortexNotFoundError, CortexValidationError

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
) -> Dict[str, Any]:
    """
    Delete a file - direct Core service call.

    Args:
        file_id: File ID to delete
        environment_id: Environment ID
        cascade: If true, delete dependent data sources and metrics

    Returns:
        Dictionary with dependencies if they exist (for 409 Conflict response)
        or None if deletion succeeded

    Raises:
        CortexNotFoundError: If file doesn't exist
        CortexValidationError: If file has dependencies and cascade=False
    """
    try:
        service = FileStorageService()
        service.delete_file(file_id, environment_id, cascade=cascade)
        return None
    except FileDoesNotExistError as e:
        raise CortexNotFoundError(str(e))
    except FileHasDependenciesError as e:
        # Get dependencies through service layer
        service = FileStorageService()
        dependencies = service.get_dependencies(file_id)
        error_data = {
            "error": "FileHasDependencies",
            "message": str(e),
            "file_id": str(file_id),
            "dependencies": {
                "data_sources": [
                    {
                        "id": str(ds["id"]),
                        "name": ds["name"],
                        "alias": ds["alias"],
                        "metrics": [
                            {
                                "id": str(m["id"]),
                                "name": m["name"],
                                "alias": m["alias"],
                                "version_count": m.get("version_count", 0)
                            }
                            for m in ds["metrics"]
                        ]
                    }
                    for ds in dependencies["data_sources"]
                ]
            }
        }
        # Raise validation error with structured dependencies
        raise CortexValidationError(str(e), details=error_data)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
