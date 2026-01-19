from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from pydantic import BaseModel

from cortex.api.schemas.requests.data_sources import DataSourceCreateRequest, DataSourceUpdateRequest
from cortex.api.schemas.responses.data_sources import DataSourceResponse
from cortex.core.connectors.api.sheets.exceptions import StorageFileAlreadyExists
from cortex.core.connectors.api.sheets.service import CortexSpreadsheetService
from cortex.core.connectors.api.sheets.types import CortexCSVFileConfig
from cortex.core.connectors.databases.SQL.humanizer import SchemaHumanizer
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.data.sources.data_sources import DataSource
from cortex.core.exceptions.data.sources import DataSourceAlreadyExistsError, DataSourceDoesNotExistError
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
        
        # Handle spreadsheet data sources - convert CSV to SQLite
        if source_type == 'spreadsheet':
            provider_type = config.get('provider_type')
            if provider_type == 'csv':
                # Get the uploaded file using file_id
                file_id = config.get('file_id')
                if not file_id:
                    raise ValueError("file_id is required for CSV provider")
                
                file_storage_service = FileStorageService()
                try:
                    from uuid import UUID
                    file_id_uuid = UUID(file_id) if isinstance(file_id, str) else file_id
                    file_record = file_storage_service.get_file(file_id_uuid, data_source_data.environment_id)
                    if not file_record:
                        raise ValueError(f"File not found: {file_id}")
                except Exception as e:
                    raise ValueError(f"Failed to retrieve file: {str(e)}")
                
                # Create CSV config from the uploaded file
                csv_file_config = CortexCSVFileConfig(
                    filename=f"{file_record.name}.{file_record.extension}",
                    file_path=file_record.path,  # This is already decrypted by get_file()
                    source_type="upload"
                )
                
                # Build config for the manager
                spreadsheet_config = {
                    'provider_type': 'csv',
                    'files': [csv_file_config.model_dump()],
                }
            
                # Create the spreadsheet data source (converts CSV to SQLite)
                source_id = str(data_source_data.alias)  # Use alias as source_id
                result = CortexSpreadsheetService.create_data_source(
                    source_id=source_id,
                    provider_type=provider_type,
                    config=spreadsheet_config,
                    selected_sheets=None  # Import all sheets by default
                )
                
                if not result['success']:
                    raise Exception(f"Failed to create spreadsheet data source: {result.get('error')}")
                
                # Get the SQLite path from the result
                sqlite_path = result['config'].get('sqlite_path')
                if not sqlite_path:
                    raise Exception("SQLite path not generated during spreadsheet conversion")
                
                # For query engine, we need a local file path
                # If using GCS (gs:// path), resolve to local cache; otherwise use as-is
                file_path_for_query = sqlite_path
                if sqlite_path.startswith('gs://'):
                    # For GCS, download/cache the file and get local path
                    from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
                    from cortex.core.connectors.api.sheets.config import get_sheets_config
                    from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend
                    
                    sheets_config = get_sheets_config()
                    cache_manager = CortexFileStorageCacheManager(
                        cache_dir=sheets_config.cache_dir,
                        max_size_gb=sheets_config.cache_max_size_gb
                    )
                    gcs_backend = CortexFileStorageGCSBackend(
                        bucket_name=sheets_config.gcs_bucket,
                        prefix=sheets_config.gcs_prefix,
                        cache_manager=cache_manager
                    )
                    
                    # Extract blob path from gs:// URI
                    # Format: gs://bucket/prefix/sqlite/source_id.db
                    blob_path = sqlite_path.replace(f"gs://{sheets_config.gcs_bucket}/", "")
                    
                    # Get local cached path (downloads if not cached)
                    file_path_for_query = cache_manager.get_cached_path(
                        file_id=str(data_source_data.alias),
                        remote_path=blob_path,
                        storage_backend=gcs_backend
                    )
                
                # Transform config to SQLite format so the query engine can use it directly
                # Since the CSV has been converted to SQLite, we change source_type to 'sqlite'
                config = {
                    'dialect': 'sqlite',
                    'file_path': file_path_for_query,
                    # Keep spreadsheet metadata for reference/refresh
                    'provider_type': provider_type,
                    'selected_sheets': result['config'].get('selected_sheets', []),
                    'table_mappings': result['config'].get('table_mappings', {}),
                    'table_hashes': result['config'].get('table_hashes', {}),
                    'last_synced': result['config'].get('last_synced'),
                    # Store the canonical GCS path for reference/refresh
                    'sqlite_path': sqlite_path,
                }
                
                # Change source_type to sqlite since we now have a SQLite DB
                source_type = 'sqlite'
        
        data_source = DataSource(
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
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
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
        if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE, DataSourceTypes.SQLITE]:
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
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Data Sources"]
)
async def delete_data_source(data_source_id: UUID):
    """Delete a data source"""
    try:
        if DataSourceCRUD.delete_data_source(data_source_id):
            return None
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete data source"
        )
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
        if data_source.source_type != DataSourceTypes.SQLITE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data source is not a spreadsheet (must be SQLITE type)"
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