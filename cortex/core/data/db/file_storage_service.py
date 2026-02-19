"""
File data source service for building spreadsheet-based data sources.

Contains:
- Pydantic models for spreadsheet configuration
- FileDataSourceService for orchestrating CSV/spreadsheet to SQLite conversion
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import Field

from cortex.core.services.data.sources.files import FileStorageService
from cortex.core.types.telescope import TSModel

if TYPE_CHECKING:
    from cortex.core.connectors.api.sheets.types import CortexCSVFileConfig


# ============================================================================
# Pydantic Models for Spreadsheet Data Source Building
# ============================================================================


class CSVProviderConfig(TSModel):
    """Configuration for CSV provider"""
    provider_type: str = Field(default='csv')
    files: List[CortexCSVFileConfig]
    environment_id: Optional[UUID] = None


class ConversionResult(TSModel):
    """Result from spreadsheet to SQLite conversion"""
    success: bool
    sqlite_path: str
    selected_sheets: List[str]
    table_mappings: Dict[str, str]  # original_name -> safe_name
    table_hashes: Dict[str, str]  # original_name -> hash
    last_synced: str


class SQLiteDataSourceConfig(TSModel):
    """Final SQLite data source configuration"""
    dialect: str = Field(default='sqlite')
    file_path: str  # Local path for query engine
    file_id: UUID  # Original file ID for dependency tracking
    provider_type: str  # 'csv' or 'gsheets'
    selected_sheets: List[str]
    table_mappings: Dict[str, str]
    table_hashes: Dict[str, str]
    last_synced: str
    sqlite_path: str  # Canonical path (GCS or local)


# ============================================================================
# File Data Source Service
# ============================================================================


class FileDataSourceService:
    """Service for building spreadsheet-based data sources"""

    @staticmethod
    def validate(file_id: UUID, environment_id: UUID):
        """
        Validate that a file exists and belongs to the environment.

        Args:
            file_id: File ID to validate
            environment_id: Environment ID for multi-tenancy

        Returns:
            CortexFileStorage model with decrypted path

        Raises:
            FileDoesNotExistError: If file not found
        """
        # Use FileStorageService to get file
        service = FileStorageService()
        file_record = service.get_file(file_id, environment_id)
        return file_record

    @staticmethod
    def get_file_config(file_record) -> CSVProviderConfig:
        """
        Create CSV provider configuration from file record.

        Args:
            file_record: CortexFileStorage model

        Returns:
            CSVProviderConfig with typed configuration
        """
        # Lazy import to avoid circular dependencies
        from cortex.core.connectors.api.sheets.types import CortexCSVFileConfig

        filename = f"{file_record.name}.{file_record.extension}"

        csv_file = CortexCSVFileConfig(
            filename=filename,
            file_path=file_record.path,  # Already decrypted by get_file()
            source_type="upload"
        )

        return CSVProviderConfig(
            provider_type='csv',
            files=[csv_file]
        )

    @staticmethod
    def convert_sqlite(
        source_id: str,
        provider_type: str,
        spreadsheet_config: CSVProviderConfig,
        selected_sheets: Optional[List[str]] = None,
        environment_id: Optional[UUID] = None
    ) -> ConversionResult:
        """
        Convert spreadsheet to SQLite database.

        Args:
            source_id: Data source identifier
            provider_type: 'csv' or 'gsheets'
            spreadsheet_config: CSV provider configuration
            selected_sheets: Optional sheet selection
            environment_id: Environment ID for hierarchical storage

        Returns:
            ConversionResult with conversion metadata

        Raises:
            Exception: If conversion fails
        """
        from cortex.core.connectors.api.sheets.service import CortexSpreadsheetService

        # Convert Pydantic model to dict for the service
        config_dict = spreadsheet_config.model_dump()

        # Add environment_id to config for hierarchical path generation
        if environment_id:
            config_dict['environment_id'] = environment_id

        # Call spreadsheet service
        result = CortexSpreadsheetService.create_data_source(
            source_id=source_id,
            provider_type=provider_type,
            config=config_dict,
            selected_sheets=selected_sheets
        )

        # Check if conversion succeeded
        if not result.get("success"):
            error_msg = result.get("error", "Unknown conversion error")
            raise Exception(f"Spreadsheet conversion failed: {error_msg}")

        # Extract config from result
        config = result.get("config", {})

        # Build typed ConversionResult
        return ConversionResult(
            success=result["success"],
            sqlite_path=config["sqlite_path"],
            selected_sheets=config["selected_sheets"],
            table_mappings=config["table_mappings"],
            table_hashes=config["table_hashes"],
            last_synced=config["last_synced"]
        )

    @staticmethod
    def resolve_sqlite_path(sqlite_path: str, source_id: str) -> str:
        """
        Resolve SQLite path for query engine access.

        For local paths: returns as-is
        For GCS paths: downloads to local cache and returns cached path

        Args:
            sqlite_path: Path from conversion (local or gs://)
            source_id: Data source identifier for cache key

        Returns:
            Local file path accessible by SQLite query engine
        """
        # If not GCS path, return as-is
        if not sqlite_path.startswith('gs://'):
            return sqlite_path

        # For GCS paths, set up cache manager
        from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend
        from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
        from cortex.core.connectors.api.sheets.config import get_sheets_config

        config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=config.cache_dir,
            sqlite_dir=config.sqlite_storage_path,
            max_size_gb=config.cache_max_size_gb
        )

        # Create GCS backend with cache manager
        gcs_backend = CortexFileStorageGCSBackend(
            bucket_name=config.gcs_bucket,
            prefix=config.gcs_prefix,
            cache_manager=cache_manager
        )

        # Extract blob path from gs:// URI
        # Format: gs://bucket/prefix/path/file.db
        blob_path = sqlite_path.replace(f'gs://{config.gcs_bucket}/', '')

        # Download to cache and get local path
        local_path = cache_manager.get_cached_path(
            file_id=source_id,
            remote_path=blob_path,
            storage_backend=gcs_backend
        )

        return local_path

    @staticmethod
    def _build_config(
        file_id: UUID,
        provider_type: str,
        local_sqlite_path: str,
        conversion: ConversionResult
    ) -> SQLiteDataSourceConfig:
        """
        Build final SQLite data source configuration.

        Args:
            file_id: Original uploaded file ID
            provider_type: 'csv' or 'gsheets'
            local_sqlite_path: Local path for query engine
            conversion: Conversion result with metadata

        Returns:
            SQLiteDataSourceConfig with all fields
        """
        return SQLiteDataSourceConfig(
            dialect='sqlite',
            file_path=local_sqlite_path,
            file_id=file_id,
            provider_type=provider_type,
            selected_sheets=conversion.selected_sheets,
            table_mappings=conversion.table_mappings,
            table_hashes=conversion.table_hashes,
            last_synced=conversion.last_synced,
            sqlite_path=conversion.sqlite_path
        )

    @staticmethod
    def build(
        file_id: UUID,
        environment_id: UUID,
        source_alias: str,
        selected_sheets: Optional[List[str]] = None
    ) -> SQLiteDataSourceConfig:
        """
        Build a spreadsheet data source from an uploaded file.

        Main orchestration method that coordinates all conversion steps.

        Args:
            file_id: Uploaded file ID (used for input file path: workspace/env/file_id.csv)
            environment_id: Environment ID for hierarchical storage
            source_alias: Data source ID (UUID) for SQLite file paths (workspace/env/data_source_id.db)
                         IMPORTANT: Should be data_source.id, NOT user-provided alias.
                         Using system-generated UUIDs prevents path injection and ensures stable file paths.
            selected_sheets: Optional sheet selection (None = all sheets)

        Returns:
            SQLiteDataSourceConfig with complete configuration

        Raises:
            FileDoesNotExistError: If file not found
            Exception: If conversion fails

        Security Note:
            The source_alias parameter determines the SQLite file path. Always use system-generated
            UUIDs (data_source.id), never user input, to prevent path injection vulnerabilities.
        """
        # 1. Validate file exists
        file_record = FileDataSourceService.validate(file_id, environment_id)

        # 2. Create CSV provider config
        provider_config = FileDataSourceService.get_file_config(file_record)

        # 3. Convert to SQLite
        conversion = FileDataSourceService.convert_sqlite(
            source_id=source_alias,
            provider_type='csv',
            spreadsheet_config=provider_config,
            selected_sheets=selected_sheets,
            environment_id=environment_id
        )

        # 4. Resolve local path for query engine
        local_path = FileDataSourceService.resolve_sqlite_path(
            conversion.sqlite_path,
            source_alias
        )

        # 5. Build final config
        config = FileDataSourceService._build_config(
            file_id=file_id,
            provider_type='csv',
            local_sqlite_path=local_path,
            conversion=conversion
        )

        return config
