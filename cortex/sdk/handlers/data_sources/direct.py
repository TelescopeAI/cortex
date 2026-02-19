"""
Data sources direct handler - Core service calls.

Handles data source operations in Direct mode.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.connectors.databases.SQL.humanizer import SchemaHumanizer
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.services import DataSourceSchemaService
from cortex.core.connectors.api.sheets.service import CortexSpreadsheetService
from cortex.core.data.db.file_storage_service import FileDataSourceService
from cortex.core.types.databases import DataSourceTypes
from cortex.core.data.sources.data_sources import DataSource
from cortex.sdk.schemas.requests.data_sources import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceRebuildRequest
)
from cortex.sdk.schemas.responses.data_sources import (
    DataSourceResponse,
    DataSourceRebuildResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_data_source(request: DataSourceCreateRequest) -> DataSourceResponse:
    """
    Create a new data source - direct Core service call.

    Args:
        request: Data source creation request

    Returns:
        Created data source response
    """
    try:
        from uuid import uuid4

        # Pre-generate UUID for consistent file naming
        data_source_id = uuid4()

        config = dict(request.config)
        source_type = request.source_type

        # Handle spreadsheet data sources - convert CSV to SQLite
        if source_type == 'spreadsheet':
            provider_type = config.get('provider_type')
            if provider_type == 'csv':
                file_id = config.get('file_id')
                if not file_id:
                    raise ValueError("file_id is required for CSV provider")

                file_id_uuid = UUID(file_id) if isinstance(file_id, str) else file_id

                # Build spreadsheet data source using service
                sqlite_config = FileDataSourceService.build(
                    file_id=file_id_uuid,
                    environment_id=request.environment_id,
                    source_alias=str(data_source_id),
                    selected_sheets=None
                )

                config = sqlite_config.model_dump()

        # Create data source with pre-generated ID
        data_source = DataSource(
            id=data_source_id,
            environment_id=request.environment_id,
            name=request.name,
            alias=request.alias,
            description=request.description,
            source_catalog=request.source_catalog,
            source_type=source_type,
            config=config
        )

        created_source = DataSourceCRUD.add_data_source(data_source)
        return DataSourceResponse(**created_source.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_data_source(data_source_id: UUID) -> DataSourceResponse:
    """
    Get a data source by ID - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Data source response
    """
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        return DataSourceResponse(**data_source.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_data_sources(environment_id: UUID) -> List[DataSourceResponse]:
    """
    List all data sources in an environment - direct Core service call.

    Args:
        environment_id: Environment ID

    Returns:
        List of data source responses
    """
    try:
        data_sources = DataSourceCRUD.get_data_sources_by_environment(environment_id)
        return [DataSourceResponse(**ds.model_dump()) for ds in data_sources]
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_data_source(
    data_source_id: UUID,
    request: DataSourceUpdateRequest
) -> DataSourceResponse:
    """
    Update a data source - direct Core service call.

    Args:
        data_source_id: Data source ID
        request: Update request

    Returns:
        Updated data source response
    """
    try:
        existing_source = DataSourceCRUD.get_data_source(data_source_id)

        # Update only provided fields
        if request.name is not None:
            existing_source.name = request.name
        if request.alias is not None:
            existing_source.alias = request.alias
        if request.description is not None:
            existing_source.description = request.description
        if request.config is not None:
            existing_source.config = request.config

        updated_source = DataSourceCRUD.update_data_source(existing_source)
        return DataSourceResponse(**updated_source.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_data_source(data_source_id: UUID, cascade: bool = False) -> None:
    """
    Delete a data source - direct Core service call.

    Args:
        data_source_id: Data source ID
        cascade: If true, delete all dependent metrics
    """
    try:
        DataSourceCRUD.delete_data_source(data_source_id, cascade=cascade)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def ping_data_source(data_source_id: UUID) -> Dict[str, Any]:
    """
    Test connectivity to a data source - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Ping result dictionary
    """
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        config = data_source.config

        # Add dialect for SQL databases if not present
        if data_source.source_type in [
            DataSourceTypes.POSTGRESQL,
            DataSourceTypes.MYSQL,
            DataSourceTypes.ORACLE,
            DataSourceTypes.SQLITE,
            DataSourceTypes.SPREADSHEET
        ]:
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
    except Exception as e:
        # Connection failed
        return {
            "status": "failed",
            "message": f"Failed to connect to data source: {str(e)}",
            "data_source_id": data_source_id,
            "error": str(e)
        }


def get_data_source_schema(data_source_id: UUID) -> Dict[str, Any]:
    """
    Get the schema information for a data source - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Schema information dictionary
    """
    try:
        service = DataSourceSchemaService()
        return service.get_schema(data_source_id)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_data_source_schema_humanized(data_source_id: UUID) -> Dict[str, Any]:
    """
    Get a human-readable description of the data source schema - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Humanized schema information dictionary
    """
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)
        config = data_source.config.copy()

        # Add dialect for SQL databases if not present
        if data_source.source_type in [
            DataSourceTypes.POSTGRESQL,
            DataSourceTypes.MYSQL,
            DataSourceTypes.ORACLE,
            DataSourceTypes.SQLITE,
            DataSourceTypes.SPREADSHEET
        ]:
            config["dialect"] = data_source.source_type

        # Create database client and get schema
        client = DBClientService.get_client(details=config, db_type=data_source.source_type)
        client.connect()
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
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def rebuild_data_source(
    data_source_id: UUID,
    request: DataSourceRebuildRequest
) -> DataSourceRebuildResponse:
    """
    Rebuild a spreadsheet data source from its original file - direct Core service call.

    Args:
        data_source_id: Data source ID
        request: Rebuild request

    Returns:
        Rebuild response
    """
    from datetime import datetime
    import pytz

    try:
        # Get data source
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        # Validate it's a spreadsheet type
        if data_source.source_type != DataSourceTypes.SPREADSHEET:
            raise ValueError(
                f"Data source is not a spreadsheet type (found: {data_source.source_type})"
            )

        # Extract provider_type and file_id from config
        provider_type = data_source.config.get("provider_type")
        if not provider_type:
            raise ValueError("Data source missing provider_type in config")

        file_id = data_source.config.get("file_id")
        if not file_id:
            raise ValueError("Data source missing file_id - cannot rebuild")

        file_id_uuid = UUID(file_id) if isinstance(file_id, str) else file_id

        # Validate original file still exists
        FileDataSourceService.validate(file_id_uuid, data_source.environment_id)

        # Optionally clear cache
        if request.clear_cache:
            old_sqlite_path = data_source.config.get("sqlite_path")
            if old_sqlite_path:
                _clear_sqlite_cache(data_source_id, old_sqlite_path)

        # Rebuild using builder service
        new_config = FileDataSourceService.build(
            file_id=file_id_uuid,
            environment_id=data_source.environment_id,
            source_alias=str(data_source.id),
            selected_sheets=data_source.config.get("selected_sheets")
        )

        # Update data source config
        data_source.config = new_config.model_dump()
        data_source.updated_at = datetime.now(pytz.UTC)
        updated_source = DataSourceCRUD.update_data_source(data_source)

        return DataSourceRebuildResponse(
            success=True,
            message=f"Successfully rebuilt data source '{data_source.name}'",
            rebuilt_tables=list(new_config.table_mappings.keys()),
            last_synced=new_config.last_synced,
            sqlite_path=new_config.sqlite_path
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def refresh_spreadsheet_source(data_source_id: UUID) -> Dict[str, Any]:
    """
    Refresh a spreadsheet data source - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Refresh result dictionary
    """
    try:
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        # Check if it's a spreadsheet type
        if data_source.source_type != DataSourceTypes.SPREADSHEET:
            raise ValueError("Data source is not a spreadsheet (must be SPREADSHEET type)")

        provider_type = data_source.config.get("provider_type")
        if not provider_type:
            raise ValueError("Data source is not a spreadsheet (missing provider_type)")

        # Refresh the source
        result = CortexSpreadsheetService.refresh_data_source(
            source_id=str(data_source_id),
            provider_type=provider_type,
            config=data_source.config,
        )

        if not result.get("success"):
            raise ValueError(result.get("error", "Unknown error during refresh"))

        # Update the data source config with new state
        data_source.config = result.get("updated_config", data_source.config)
        DataSourceCRUD.update_data_source(data_source)

        return {
            "refreshed_tables": result.get("refreshed_tables", []),
            "unchanged_tables": result.get("unchanged_tables", []),
            "last_synced": result.get("updated_config", {}).get("last_synced")
        }
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_spreadsheet_status(data_source_id: UUID) -> Dict[str, Any]:
    """
    Get sync status and table list for a spreadsheet data source - direct Core service call.

    Args:
        data_source_id: Data source ID

    Returns:
        Status information dictionary
    """
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
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def _clear_sqlite_cache(data_source_id: UUID, sqlite_path: str) -> None:
    """
    Clear SQLite cache entries and physical files (best-effort).

    Args:
        data_source_id: Data source ID
        sqlite_path: Path to SQLite file (local or gs://)
    """
    import logging
    import os
    import sqlite3

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


def discover_sheets(provider_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Discover available sheets from a provider - direct Core service call.

    Args:
        provider_type: Provider type (e.g., "csv", "gsheets")
        config: Provider configuration

    Returns:
        Dictionary with available tables/sheets

    Raises:
        CortexSDKError: On discovery failure
    """
    try:
        result = CortexSpreadsheetService.discover_sheets(
            provider_type=provider_type,
            config=config,
        )
        return result
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def preview_sheet(
    provider_type: str,
    config: Dict[str, Any],
    sheet_name: str,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Preview data from a sheet - direct Core service call.

    Args:
        provider_type: Provider type (e.g., "csv", "gsheets")
        config: Provider configuration
        sheet_name: Name of the sheet/table to preview
        limit: Number of rows to preview

    Returns:
        Dictionary with preview data (columns, rows, total_rows)

    Raises:
        CortexSDKError: On preview failure
    """
    try:
        result = CortexSpreadsheetService.preview_sheet(
            provider_type=provider_type,
            config=config,
            sheet_name=sheet_name,
            limit=limit,
        )
        return result
    except Exception as e:
        raise CoreExceptionMapper().map(e)
