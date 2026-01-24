from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.core.connectors.api.sheets.converter import CortexSQLiteConverter
from cortex.core.connectors.api.sheets.providers.base import CortexSpreadsheetProvider
from cortex.core.connectors.api.sheets.providers.csv import CortexCSVProvider
from cortex.core.connectors.api.sheets.providers.gsheets import CortexGoogleSheetsProvider
from cortex.core.connectors.api.sheets.storage.base import CortexFileStorageBackend
from cortex.core.connectors.api.sheets.storage.local import CortexLocalFileStorage
from cortex.core.connectors.api.sheets.tracker import CortexRefreshTracker
from cortex.core.connectors.api.sheets.types import CortexSheetMetadata, CortexCSVFileConfig
from cortex.core.connectors.api.sheets.types import CortexSheetsStorageType
from cortex.core.services.data.sources.files_config import (
    get_file_storage_config,
    default_sqlite_path_generator,
)


class CortexSpreadsheetManager:
    """Orchestrates spreadsheet data source operations"""
    
    def __init__(self, source_id: str, storage_backend: Optional[CortexFileStorageBackend] = None):
        """
        Initialize manager
        
        Args:
            source_id: Unique identifier for the data source
            storage_backend: Storage backend (defaults to auto-selected based on config)
        """
        self.source_id = str(source_id)
        
        # Auto-select storage backend if not provided
        if storage_backend is None:
            config = get_sheets_config()
            
            if config.storage_type == CortexSheetsStorageType.GCS:
                from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend
                
                cache_manager = CortexFileStorageCacheManager(
                    cache_dir=config.cache_dir,
                    max_size_gb=config.cache_max_size_gb
                )
                
                storage_backend = CortexFileStorageGCSBackend(
                    bucket_name=config.gcs_bucket,
                    prefix=config.gcs_prefix,
                    cache_manager=cache_manager
                )
            else:
                storage_backend = CortexLocalFileStorage()
        
        self.storage_backend = storage_backend
        self.refresh_tracker = CortexRefreshTracker()
    
    def get_available_sheets(
        self,
        provider_type: str,
        config: Dict[str, Any]
    ) -> List[CortexSheetMetadata]:
        """
        Get list of available sheets from a provider
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            
        Returns:
            List of available sheets
        """
        provider = self._create_provider(provider_type, config)
        return provider.list_sheets()
    
    def preview_sheet(
        self,
        provider_type: str,
        config: Dict[str, Any],
        sheet_name: str,
        limit: int = 100
    ) -> Dict:
        """
        Preview data from a sheet
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            sheet_name: Name of the sheet to preview
            limit: Maximum rows to preview
            
        Returns:
            Preview data
        """
        provider = self._create_provider(provider_type, config)
        preview = provider.preview_sheet(sheet_name, limit)
        return {
            "columns": preview.columns,
            "rows": preview.rows,
            "total_rows": preview.total_rows,
        }
    
    def create_data_source(
        self,
        provider_type: str,
        config: Dict[str, Any],
        selected_sheets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a data source by downloading and converting sheets to SQLite
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            selected_sheets: Which sheets to import (None = all)
            
        Returns:
            Updated config with sqlite_path and other metadata
        """
        # Create provider
        provider = self._create_provider(provider_type, config)
        
        # Download selected sheets as CSV
        available_sheets = provider.list_sheets()
        available_names = [s.name for s in available_sheets]
        
        # Determine which sheets to download
        sheets_to_download = selected_sheets if selected_sheets else available_names
        
        # Download as CSV
        csv_data = provider.download_selected(sheets_to_download)
        
        # Create converter and convert to SQLite
        sqlite_path_generator = None
        environment_id = config.get("environment_id")
        if environment_id:
            if not isinstance(environment_id, UUID):
                environment_id = UUID(str(environment_id))
            storage_config = get_file_storage_config()
            generator = storage_config.sqlite_path_generator or default_sqlite_path_generator
            sqlite_path_generator = lambda source_id: generator(environment_id, source_id)

        sqlite_path = self.storage_backend.get_sqlite_path(
            self.source_id,
            path_generator=sqlite_path_generator,
        )
        converter = CortexSQLiteConverter(sqlite_path)
        
        # Convert CSVs to SQLite tables
        table_mappings = converter.convert_from_csv_data(csv_data, sheets_to_download)

        # Save SQLite to storage backend (uploads to GCS if using GCS backend)
        # The converter creates a local SQLite file, we need to save it to the backend storage
        saved_sqlite_path = self.storage_backend.save_sqlite(self.source_id, sqlite_path)

        # Compute hashes for refresh tracking
        table_hashes = {}
        for original_name, safe_name in table_mappings.items():
            hash_val = converter.get_table_hash(safe_name)
            table_hashes[original_name] = hash_val
            self.refresh_tracker.update_table_hash(original_name, hash_val)

        # Ensure last_synced is set even if no tables were processed
        if self.refresh_tracker.last_synced is None:
            self.refresh_tracker.last_synced = datetime.utcnow().isoformat()
        
        # Build updated config
        updated_config = config.copy()
        updated_config.update({
            "provider_type": provider_type,
            "selected_sheets": sheets_to_download,
            "sqlite_path": saved_sqlite_path,  # Use the saved path (which may be in GCS)
            "table_mappings": table_mappings,
            "table_hashes": table_hashes,
            "last_synced": self.refresh_tracker.last_synced,
        })
        
        return updated_config
    
    def refresh_data_source(
        self,
        provider_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Refresh a data source by checking for changes and updating modified sheets
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Data source configuration
            
        Returns:
            Update results with refreshed tables
        """
        # Restore tracker state from config
        if "table_hashes" in config:
            self.refresh_tracker.restore_state({
                "table_hashes": config.get("table_hashes", {}),
                "last_synced": config.get("last_synced"),
            })
        
        # Create provider and download current sheets
        provider = self._create_provider(provider_type, config)
        
        selected_sheets = config.get("selected_sheets", [])
        csv_data = provider.download_selected(selected_sheets)
        
        # Compute current hashes
        sqlite_path = config.get("sqlite_path")
        if not sqlite_path:
            sqlite_path_generator = None
            environment_id = config.get("environment_id")
            if environment_id:
                if not isinstance(environment_id, UUID):
                    environment_id = UUID(str(environment_id))
                storage_config = get_file_storage_config()
                generator = storage_config.sqlite_path_generator or default_sqlite_path_generator
                sqlite_path_generator = lambda source_id: generator(environment_id, source_id)

            sqlite_path = self.storage_backend.get_sqlite_path(
                self.source_id,
                path_generator=sqlite_path_generator,
            )
        converter = CortexSQLiteConverter(sqlite_path)
        
        current_hashes = {}
        for sheet_name in selected_sheets:
            if sheet_name in csv_data:
                # Create temp converter to compute hash
                temp_converter = CortexSQLiteConverter(sqlite_path)
                table_mappings = temp_converter.convert_from_csv_data({sheet_name: csv_data[sheet_name]})
                
                if sheet_name in table_mappings:
                    safe_name = table_mappings[sheet_name]
                    hash_val = converter.get_table_hash(safe_name)
                    current_hashes[sheet_name] = hash_val
        
        # Get tables that need refresh
        tables_to_refresh = self.refresh_tracker.get_tables_to_refresh(current_hashes)
        
        # If tables need refresh, update them
        if tables_to_refresh:
            csv_data_for_refresh = {k: v for k, v in csv_data.items() if k in tables_to_refresh}
            converter.convert_from_csv_data(csv_data_for_refresh)
            
            # Save updated SQLite to storage backend (uploads to GCS if using GCS backend)
            saved_sqlite_path = self.storage_backend.save_sqlite(self.source_id, sqlite_path)
            
            # Update hashes
            for table_name in tables_to_refresh:
                self.refresh_tracker.update_table_hash(table_name, current_hashes[table_name])
        else:
            # Even if no tables need refresh, make sure SQLite is saved to backend
            saved_sqlite_path = self.storage_backend.save_sqlite(self.source_id, sqlite_path)
        
        # Get unchanged tables
        unchanged_tables = [s for s in selected_sheets if s not in tables_to_refresh]

        # Ensure last_synced is set
        if self.refresh_tracker.last_synced is None:
            self.refresh_tracker.last_synced = datetime.utcnow().isoformat()

        # Update config
        updated_config = config.copy()
        updated_config.update({
            "sqlite_path": saved_sqlite_path,  # Use the saved path (which may be in GCS)
            "table_hashes": self.refresh_tracker.table_hashes,
            "last_synced": self.refresh_tracker.last_synced,
        })
        
        return {
            "refreshed_tables": tables_to_refresh,
            "unchanged_tables": unchanged_tables,
            "updated_config": updated_config,
        }
    
    def _create_provider(self, provider_type: str, config: Dict[str, Any]) -> CortexSpreadsheetProvider:
        """
        Create appropriate provider based on type
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            
        Returns:
            Provider instance
        """
        if provider_type == "csv":
            # Parse CSV credentials from config
            if "files" in config:
                files = [CortexCSVFileConfig(**f) if isinstance(f, dict) else f for f in config["files"]]
            else:
                files = []
            
            # Pass storage backend so it can read remote files (GCS, S3, etc.)
            return CortexCSVProvider(files, self.source_id, storage_backend=self.storage_backend)
        
        elif provider_type == "gsheets":
            # Parse Google Sheets credentials from config
            spreadsheet_id = config.get("spreadsheet_id")
            service_account_json = config.get("service_account_json")
            access_token = config.get("access_token")
            
            if not spreadsheet_id:
                raise ValueError("spreadsheet_id is required for gsheets provider")
            
            return CortexGoogleSheetsProvider(
                spreadsheet_id=spreadsheet_id,
                service_account_json=service_account_json,
                access_token=access_token,
                source_id=self.source_id,
            )
        
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
