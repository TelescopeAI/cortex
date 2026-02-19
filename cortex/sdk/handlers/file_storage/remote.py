"""
Remote mode implementations for file storage operations.

Makes HTTP API calls to remote Cortex server.
"""
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient


def upload_files(
    client: CortexHTTPClient,
    environment_id: UUID,
    files: List[Tuple[str, bytes]],
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Upload files - HTTP API call.

    Args:
        client: HTTP client instance
        environment_id: Environment ID
        files: List of (filename, content) tuples
        overwrite: Whether to overwrite existing files

    Returns:
        Dictionary with uploaded file information
    """
    # For now, upload one file at a time (API might not support batch)
    # TODO: Check if API supports multiple file upload in one request
    uploaded_files = []

    for filename, content in files:
        params = {
            "environment_id": str(environment_id),
            "overwrite": str(overwrite).lower()
        }
        response = client.upload_file(
            "/data/sources/upload",
            file=content,
            filename=filename,
            params=params
        )
        uploaded_files.extend(response.get("files", []))

    return {
        "file_ids": [f["id"] for f in uploaded_files],
        "files": uploaded_files,
        "message": f"Uploaded {len(uploaded_files)} file(s)"
    }


def list_files(
    client: CortexHTTPClient,
    environment_id: UUID,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    List uploaded files - HTTP API call.

    Args:
        client: HTTP client instance
        environment_id: Environment ID
        limit: Optional limit on number of files

    Returns:
        Dictionary with list of files
    """
    params = {"environment_id": str(environment_id)}
    if limit is not None:
        params["limit"] = limit

    response = client.get("/data/sources/files", params=params)
    return response


def delete_file(
    client: CortexHTTPClient,
    file_id: UUID,
    environment_id: UUID,
    cascade: bool = False
) -> None:
    """
    Delete a file - HTTP API call.

    Args:
        client: HTTP client instance
        file_id: File ID to delete
        environment_id: Environment ID
        cascade: If true, delete dependent data sources and metrics
    """
    params = {
        "environment_id": str(environment_id),
        "cascade": str(cascade).lower()
    }
    client.delete(f"/data/sources/files/{file_id}", params=params)
