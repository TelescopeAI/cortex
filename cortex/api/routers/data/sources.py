import os
import sqlite3
from datetime import datetime
from http import HTTPStatus
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

import pytz
from fastapi import APIRouter, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cortex.api.schemas.requests.data_sources import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceRebuildRequest
)
from cortex.api.schemas.responses.data_sources import (
    DataSourceResponse,
    DataSourceRebuildResponse
)
from cortex.core.connectors.api.sheets.exceptions import StorageFileAlreadyExists
from cortex.core.connectors.api.sheets.service import CortexSpreadsheetService
from cortex.core.connectors.databases.SQL.humanizer import SchemaHumanizer
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.data.db.file_storage_service import FileStorageService as FileStorageCRUD, FileDataSourceService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.data.sources.data_sources import DataSource
from cortex.core.exceptions.data.sources import (
    DataSourceAlreadyExistsError,
    DataSourceDoesNotExistError,
    DataSourceHasDependenciesError,
    FileDoesNotExistError,
    FileHasDependenciesError
)
from cortex.core.exceptions.environments import EnvironmentDoesNotExistError
from cortex.core.services import DataSourceSchemaService
from cortex.core.services.data.sources.files import FileStorageService
from cortex.core.types.databases import DataSourceTypes

DataSourcesRouter = APIRouter()


@DataSourcesRouter.post(
    "/data/sources",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Data Sources"]
)
async def create_data_source(data_source_data: DataSourceCreateRequest):
    """Create a new data source"""
    try:
        config = dict(data_source_data.config)
        source_type = data_source_data.source_type
        
        # Pre-generate UUID for this data source (used for both DB record and file paths)
        # This ensures consistent hierarchical file naming without using user input
        data_source_id = uuid4()

        # Handle spreadsheet data sources - convert CSV to SQLite
        if source_type == 'spreadsheet':
            provider_type = config.get('provider_type')
            if provider_type == 'csv':
                # Get the uploaded file using file_id
                file_id = config.get('file_id')
                if not file_id:
                    raise ValueError("file_id is required for CSV provider")

                # Convert file_id to UUID if needed
                file_id_uuid = UUID(file_id) if isinstance(file_id, str) else file_id

                # Build spreadsheet data source using service
                # Use data_source_id (UUID) instead of user alias for file paths
                sqlite_config = FileDataSourceService.build(
                    file_id=file_id_uuid,
                    environment_id=data_source_data.environment_id,
                    source_alias=str(data_source_id),
                    selected_sheets=None  # Import all sheets by default
                )

                # Convert Pydantic model to dict for data source config
                config = sqlite_config.model_dump()

        # Create DataSource with pre-generated ID (CRUD will respect it)
        data_source = DataSource(
            id=data_source_id,
            environment_id=data_source_data.environment_id,
            name=data_source_data.name,
            alias=data_source_data.alias,
            description=data_source_data.description,
            source_catalog=data_source_data.source_catalog,
            source_type=source_type,
            config=config
        )
        created_source = DataSourceCRUD.add_data_source(data_source)
        return DataSourceResponse(**created_source.model_dump())
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DataSourceAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat()
            }
            for f in files
        ]
    }


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
        if FileStorageCRUD.delete_file(file_id, environment_id, cascade=cascade):
            return None
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
    except FileDoesNotExistError as e:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(e))
    except FileHasDependenciesError as e:
        dependencies = FileStorageCRUD.get_file_dependencies(file_id)
        return JSONResponse(
            status_code=HTTPStatus.CONFLICT,
            content={
                "detail": {
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
                                        "version_count": m["version_count"]
                                    }
                                    for m in ds["metrics"]
                                ]
                            }
                            for ds in dependencies["data_sources"]
                        ]
                    }
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        return DataSourceResponse(**data_source.model_dump())
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.get(
    "/environments/{environment_id}/data/sources",
    response_model=List[DataSourceResponse],
    tags=["Environments"]
)
async def list_data_sources(environment_id: UUID):
    """List all data sources in an environment"""
    try:
        data_sources = DataSourceCRUD.get_data_sources_by_environment(environment_id)
        return [DataSourceResponse(**ds.model_dump()) for ds in data_sources]
    except EnvironmentDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.put(
    "/data/sources/{data_source_id}",
    response_model=DataSourceResponse,
    tags=["Data Sources"]
)
async def update_data_source(data_source_id: UUID, data_source_data: DataSourceUpdateRequest):
    """Update a data source"""
    try:
        # Get existing data source
        existing_source = DataSourceCRUD.get_data_source(data_source_id)

        # Update only provided fields
        if data_source_data.name is not None:
            existing_source.name = data_source_data.name
        if data_source_data.alias is not None:
            existing_source.alias = data_source_data.alias
        if data_source_data.description is not None:
            existing_source.description = data_source_data.description
        if data_source_data.config is not None:
            existing_source.config = data_source_data.config

        updated_source = DataSourceCRUD.update_data_source(existing_source)
        return DataSourceResponse(**updated_source.model_dump())
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/ping",
    tags=["Data Sources"]
)
async def ping_data_source(data_source_id: UUID):
    """Test connectivity to a data source"""
    try:
        # Get the data source configuration
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        
        # Extract connection details from config
        config = data_source.config
        
        # Add dialect for SQL databases if not present
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE, DataSourceTypes.SPREADSHEET]:
            config["dialect"] = data_source.source_type
        
        # Create database client and test connection
        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
        client.connect()
        
        return {
            "status": "success",
            "message": f"Successfully connected to data source {data_source.name}",
            "data_source_id": data_source_id,
            "data_source_name": data_source.name,
            "source_type": data_source.source_type
        }
        
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Connection failed or other error
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
        service = DataSourceSchemaService()
        return service.get_schema(data_source_id)
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Schema retrieval failed or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve schema for data source: {str(e)}"
        )


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/schema/humanized",
    tags=["Data Sources"]
)
async def get_data_source_schema_humanized(data_source_id: UUID):
    """Get a human-readable description of the data source schema"""
    try:
        # Get the data source configuration
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        
        # Extract connection details from config
        config = data_source.config.copy()
        
        # Add dialect for SQL databases if not present
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE, DataSourceTypes.SPREADSHEET]:
            config["dialect"] = data_source.source_type
        
        # Create database client and get schema
        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
        client.connect()
        
        # Get schema information
        schema = client.get_schema()
        
        # Humanize the schema
        humanizer = SchemaHumanizer()
        human_readable_schema = humanizer.humanize_schema(schema)
        
        return {
            "status": "success",
            "message": f"Successfully retrieved humanized schema for data source {data_source.name}",
            "data_source_id": data_source_id,
            "data_source_name": data_source.name,
            "source_type": data_source.source_type,
            "humanized_schema": human_readable_schema
        }
        
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        # Schema retrieval failed or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve humanized schema for data source: {str(e)}"
        )


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
        if DataSourceCRUD.delete_data_source(data_source_id, cascade=cascade):
            return None
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to delete data source"
        )
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=str(e)
        )
    except DataSourceHasDependenciesError as e:
        dependencies = DataSourceCRUD.get_data_source_dependencies(data_source_id)
        return JSONResponse(
            status_code=HTTPStatus.CONFLICT,
            content={
                "detail": {
                    "error": "DataSourceHasDependencies",
                    "message": str(e),
                    "data_source_id": str(data_source_id),
                    "dependencies": {
                        "metrics": [
                            {
                                "id": str(m["id"]),
                                "name": m["name"],
                                "alias": m["alias"],
                                "version_count": m["version_count"]
                            }
                            for m in dependencies["metrics"]
                        ]
                    }
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=str(e)
        )



# ============================================================================
# Spreadsheet Data Source Endpoints
# ============================================================================


class DiscoverRequest(BaseModel):
    """Request to discover available sheets"""
    provider_type: str  # "csv" or "gsheets"
    config: Dict[str, Any]


class DiscoverResponse(BaseModel):
    """Response with available sheets"""
    tables: List[Dict[str, Any]]


class PreviewRequest(BaseModel):
    """Request to preview sheet data"""
    provider_type: str
    config: Dict[str, Any]
    table_name: str
    limit: int = 100


class PreviewResponse(BaseModel):
    """Response with preview data"""
    columns: List[str]
    rows: List[List[Optional[str]]]
    total_rows: int


class RefreshResponse(BaseModel):
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
    
    service = FileStorageService()
    
    try:
        # Prepare files list
        files_data = []
        for file in files:
            if not file.filename:
                continue
            content = await file.read()
            files_data.append((file.filename, content))
        
        # Upload via service
        uploaded_files = service.upload_files(
            environment_id=environment_id,
            files=files_data,
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
                    "mime_type": f.mime_type
                }
                for f in uploaded_files
            ],
            "message": f"Uploaded {len(uploaded_files)} file(s)"
        }
    except StorageFileAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "StorageFileAlreadyExists",
                "filename": e.filename,
                "file_id": e.file_id,
                "message": f"File '{e.filename}' already exists"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload files: {str(e)}"
        )


@DataSourcesRouter.post(
    "/data/sources/discover",
    response_model=DiscoverResponse,
    tags=["Spreadsheets"]
)
async def discover_sheets(request: DiscoverRequest):
    """Discover available sheets from a provider"""
    try:
        result = CortexSpreadsheetService.discover_sheets(
            provider_type=request.provider_type,
            config=request.config,
        )
        return DiscoverResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover sheets: {str(e)}"
        )


@DataSourcesRouter.post(
    "/data/sources/preview",
    response_model=PreviewResponse,
    tags=["Spreadsheets"]
)
async def preview_sheet(request: PreviewRequest):
    """Preview data from a sheet"""
    try:
        result = CortexSpreadsheetService.preview_sheet(
            provider_type=request.provider_type,
            config=request.config,
            sheet_name=request.table_name,
            limit=request.limit,
        )
        return PreviewResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview sheet: {str(e)}"
        )


@DataSourcesRouter.post(
    "/data/sources/{data_source_id}/refresh",
    response_model=RefreshResponse,
    tags=["Spreadsheets"]
)
async def refresh_spreadsheet_source(data_source_id: UUID):
    """Refresh a spreadsheet data source"""
    try:
        # Get the data source
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        
        # Check if it's a spreadsheet type
        if data_source.source_type != DataSourceTypes.SPREADSHEET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source is not a spreadsheet (must be SPREADSHEET type)"
            )
        
        provider_type = data_source.config.get("provider_type")
        if not provider_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source is not a spreadsheet (missing provider_type)"
            )
        
        # Refresh the source
        result = CortexSpreadsheetService.refresh_data_source(
            source_id=str(data_source_id),
            provider_type=provider_type,
            config=data_source.config,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Unknown error during refresh")
            )
        
        # Update the data source config with new state
        data_source.config = result.get("updated_config", data_source.config)
        DataSourceCRUD.update_data_source(data_source)
        
        return RefreshResponse(
            refreshed_tables=result.get("refreshed_tables", []),
            unchanged_tables=result.get("unchanged_tables", []),
            last_synced=result.get("updated_config", {}).get("last_synced"),
        )
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh data source: {str(e)}"
        )


@DataSourcesRouter.get(
    "/data/sources/{data_source_id}/status",
    tags=["Spreadsheets"]
)
async def get_spreadsheet_status(data_source_id: UUID):
    """Get sync status and table list for a spreadsheet data source"""
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        config = data_source.config

        return {
            "source_id": str(data_source_id),
            "source_type": data_source.source_type,
            "provider_type": config.get("provider_type"),
            "selected_sheets": config.get("selected_sheets", []),
            "table_mappings": config.get("table_mappings", {}),
            "last_synced": config.get("last_synced"),
            "sqlite_path": config.get("sqlite_path"),
        }
    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Helper Functions
# ============================================================================


def _clear_sqlite_cache(data_source_id: UUID, sqlite_path: str) -> None:
    """
    Clear SQLite cache entries and physical files.

    Best-effort operation - logs errors but doesn't raise exceptions.

    Args:
        data_source_id: Data source ID (used as file_id in cache)
        sqlite_path: Path to SQLite file (local or gs://)
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # For local paths: delete physical file
        if not sqlite_path.startswith('gs://'):
            if os.path.exists(sqlite_path):
                os.remove(sqlite_path)
                logger.info(f"Deleted local SQLite file: {sqlite_path}")
            return

        # For GCS paths: clear cache entry
        from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
        from cortex.core.connectors.api.sheets.config import get_sheets_config

        config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=config.cache_dir,
            max_size_gb=config.cache_max_size_gb
        )

        # Get cached file path
        cached_path = cache_manager._get_cache_entry(str(data_source_id))

        # Delete physical cached file
        if cached_path and os.path.exists(cached_path):
            os.remove(cached_path)
            logger.info(f"Deleted cached SQLite file: {cached_path}")

        # Delete cache metadata entry
        conn = sqlite3.connect(cache_manager.metadata_db)
        conn.execute(
            "DELETE FROM files_cache_entries WHERE file_id = ?",
            (str(data_source_id),)
        )
        conn.commit()
        conn.close()
        logger.info(f"Cleared cache metadata for data source {data_source_id}")

    except Exception as e:
        # Log but don't fail - cache cleanup is best-effort
        logger.warning(f"Failed to clear cache for {data_source_id}: {e}")


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
        # 1. Get data source by ID
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        # 2. Validate it's a spreadsheet type
        if data_source.source_type != DataSourceTypes.SPREADSHEET:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data source is not a spreadsheet type (found: {data_source.source_type})"
            )

        # 3. Extract provider_type and file_id from config
        provider_type = data_source.config.get("provider_type")
        if not provider_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source missing provider_type in config"
            )

        file_id = data_source.config.get("file_id")
        if not file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source missing file_id - cannot rebuild"
            )

        file_id_uuid = UUID(file_id) if isinstance(file_id, str) else file_id

        # 4. Validate original file still exists
        try:
            FileDataSourceService.validate(file_id_uuid, data_source.environment_id)
        except FileDoesNotExistError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Original file {file_id} not found"
            )

        # 5. Optionally clear cache
        if request.clear_cache:
            old_sqlite_path = data_source.config.get("sqlite_path")
            if old_sqlite_path:
                _clear_sqlite_cache(data_source_id, old_sqlite_path)

        # 6. Rebuild using builder service
        # Use existing data_source.id (stable, never changes) instead of user alias
        new_config = FileDataSourceService.build(
            file_id=file_id_uuid,
            environment_id=data_source.environment_id,
            source_alias=str(data_source.id),
            selected_sheets=data_source.config.get("selected_sheets")
        )

        # 7. Update data source config
        data_source.config = new_config.model_dump()
        data_source.updated_at = datetime.now(pytz.UTC)
        updated_source = DataSourceCRUD.update_data_source(data_source)

        # 8. Return success response
        return DataSourceRebuildResponse(
            success=True,
            message=f"Successfully rebuilt data source '{data_source.name}'",
            rebuilt_tables=list(new_config.table_mappings.keys()),
            last_synced=new_config.last_synced,
            sqlite_path=new_config.sqlite_path
        )

    except DataSourceDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebuild data source: {str(e)}"
        )
