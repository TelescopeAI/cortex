from http import HTTPStatus
from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse

from cortex.api.schemas.requests.data_sources import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceRebuildRequest
)
from cortex.api.schemas.responses.data_sources import (
    DataSourceResponse,
    DataSourceRebuildResponse
)
from cortex.core.types.telescope import TSModel
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError

DataSourcesRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@DataSourcesRouter.post(
    "/data/sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Data Sources"]
)
async def create_data_source(data_source_data: DataSourceCreateRequest):
    """Create a new data source"""
    try:
        return _client.data_sources.create(data_source_data)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# File Management Endpoints (must come before {data_source_id} routes)
# ============================================================================

@DataSourcesRouter.get("/data/sources/files", tags=["Spreadsheets"])
async def list_uploaded_files(environment_id: UUID = None, limit: Optional[int] = None):
    """List all uploaded files for an environment"""
    if not environment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="environment_id query parameter is required"
        )

    try:
        return _client.file_storage.list(environment_id, limit)
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.delete(
    "/data/sources/files/{file_id}",
    status_code=HTTPStatus.NO_CONTENT,
    tags=["Spreadsheets"]
)
async def delete_file(
    file_id: UUID,
    environment_id: UUID,
    cascade: bool = False
):
    """
    Delete an uploaded file.

    Args:
        file_id: The ID of the file to delete
        environment_id: Environment ID for multi-tenancy validation
        cascade: If true, delete all dependent data sources and metrics (default: false)
    """
    try:
        _client.file_storage.delete(file_id, environment_id, cascade)
        return None
    except CortexNotFoundError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        # Check if this has dependency details (409 Conflict)
        if hasattr(e, 'details') and e.details and "dependencies" in e.details:
            return JSONResponse(
                status_code=HTTPStatus.CONFLICT,
                content={"detail": e.details}
            )
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# Data Source CRUD Endpoints
# ============================================================================

@DataSourcesRouter.get(
    "/data/sources/{data_source_id}",
    response_model=DataSourceResponse,
    tags=["Data Sources"]
)
async def get_data_source(data_source_id: UUID):
    """Get a data source by ID"""
    try:
        return _client.data_sources.get(data_source_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.get(
    "/environments/{environment_id}/data/sources",
    response_model=List[DataSourceResponse],
    tags=["Environments"]
)
async def list_data_sources(environment_id: UUID):
    """List all data sources in an environment"""
    try:
        return _client.data_sources.list(environment_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.put(
    "/data/sources/{data_source_id}",
    response_model=DataSourceResponse,
    tags=["Data Sources"]
)
async def update_data_source(data_source_id: UUID, data_source_data: DataSourceUpdateRequest):
    """Update a data source"""
    try:
        return _client.data_sources.update(data_source_id, data_source_data)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/ping",
    tags=["Data Sources"]
)
async def ping_data_source(data_source_id: UUID):
    """Test connectivity to a data source"""
    try:
        return _client.data_sources.ping(data_source_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        # Return failure response instead of raising for connection failures
        return {
            "status": "failed",
            "message": f"Failed to connect to data source: {str(e)}",
            "data_source_id": data_source_id,
            "error": str(e)
        }


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/schema",
    tags=["Data Sources"]
)
async def get_data_source_schema(data_source_id: UUID):
    """Get the schema information for a data source"""
    try:
        return _client.data_sources.get_schema(data_source_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/schema/humanized",
    tags=["Data Sources"]
)
async def get_data_source_schema_humanized(data_source_id: UUID):
    """Get a human-readable description of the data source schema"""
    try:
        return _client.data_sources.get_schema_humanized(data_source_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.delete(
    "/data/sources/{data_source_id}",
    status_code=HTTPStatus.NO_CONTENT,
    tags=["Data Sources"]
)
async def delete_data_source(
    data_source_id: UUID,
    cascade: bool = False
):
    """
    Delete a data source.

    Args:
        data_source_id: The ID of the data source to delete
        cascade: If true, delete all dependent metrics before deleting
                 the data source. Default is false.
    """
    try:
        _client.data_sources.delete(data_source_id, cascade=cascade)
        return None
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        # Handle dependencies error - CortexValidationError contains dependency info
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



# ============================================================================
# Spreadsheet Data Source Endpoints
# ============================================================================


class DiscoverRequest(TSModel):
    """Request to discover available sheets"""
    provider_type: str  # "csv" or "gsheets"
    config: Dict[str, Any]


class DiscoverResponse(TSModel):
    """Response with available sheets"""
    tables: List[Dict[str, Any]]


class PreviewRequest(TSModel):
    """Request to preview sheet data"""
    provider_type: str
    config: Dict[str, Any]
    table_name: str
    limit: int = 100


class PreviewResponse(TSModel):
    """Response with preview data"""
    columns: List[str]
    rows: List[List[Optional[str]]]
    total_rows: int


class RefreshResponse(TSModel):
    """Response from refresh operation"""
    refreshed_tables: List[str]
    unchanged_tables: List[str]
    last_synced: Optional[str] = None


@DataSourcesRouter.post(
    "/data/sources/upload",
    tags=["Spreadsheets"]
)
async def upload_files(
    files: List[UploadFile] = File(...),
    environment_id: UUID = None,
    overwrite: bool = False
):
    """Upload files with duplicate detection and optional overwrite"""
    if not environment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="environment_id query parameter is required"
        )

    try:
        # Prepare files list
        files_data = []
        for file in files:
            if not file.filename:
                continue
            content = await file.read()
            files_data.append((file.filename, content))

        # Upload via SDK
        return _client.file_storage.upload(environment_id, files_data, overwrite)
    except CortexValidationError as e:
        # Check for file already exists error (409 Conflict)
        if "already exists" in str(e).lower() or "StorageFileAlreadyExists" in str(e):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.post(
    "/data/sources/discover",
    response_model=DiscoverResponse,
    tags=["Spreadsheets"]
)
async def discover_sheets(request: DiscoverRequest):
    """Discover available sheets from a provider"""
    try:
        result = _client.data_sources.discover_sheets(
            provider_type=request.provider_type,
            config=request.config
        )
        return DiscoverResponse(**result)
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.post(
    "/data/sources/preview",
    response_model=PreviewResponse,
    tags=["Spreadsheets"]
)
async def preview_sheet(request: PreviewRequest):
    """Preview data from a sheet"""
    try:
        result = _client.data_sources.preview_sheet(
            provider_type=request.provider_type,
            config=request.config,
            sheet_name=request.table_name,
            limit=request.limit
        )
        return PreviewResponse(**result)
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/refresh",
    response_model=RefreshResponse,
    tags=["Spreadsheets"]
)
async def refresh_spreadsheet_source(data_source_id: UUID):
    """Refresh a spreadsheet data source"""
    try:
        result = _client.data_sources.refresh_spreadsheet(data_source_id)
        return RefreshResponse(
            refreshed_tables=result.get("refreshed_tables", []),
            unchanged_tables=result.get("unchanged_tables", []),
            last_synced=result.get("last_synced"),
        )
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/status",
    tags=["Spreadsheets"]
)
async def get_spreadsheet_status(data_source_id: UUID):
    """Get sync status and table list for a spreadsheet data source"""
    try:
        return _client.data_sources.get_spreadsheet_status(data_source_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# Rebuild Endpoint
# ============================================================================


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/rebuild",
    response_model=DataSourceRebuildResponse,
    tags=["Spreadsheets"]
)
async def rebuild_data_source(
    data_source_id: UUID,
    request: DataSourceRebuildRequest = DataSourceRebuildRequest()
):
    """
    Rebuild a spreadsheet data source from its original uploaded file.

    This operation:
    - Retrieves the original uploaded file
    - Optionally clears the SQLite cache
    - Regenerates the SQLite database
    - Updates the data source config with new metadata

    Args:
        data_source_id: ID of the data source to rebuild
        request: Rebuild configuration options

    Returns:
        Rebuild results with updated metadata

    Raises:
        404: Data source not found
        400: Data source is not a spreadsheet or missing file_id
        404: Original file not found
        500: Rebuild failed
    """
    try:
        return _client.data_sources.rebuild(data_source_id, request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
