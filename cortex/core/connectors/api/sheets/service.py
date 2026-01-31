from typing import Optional, List, Dict, Any
from uuid import UUID

from cortex.core.connectors.api.sheets.manager import CortexSpreadsheetManager


class CortexSpreadsheetService:
    """High-level service for spreadsheet data source operations"""
    
    @staticmethod
    def discover_sheets(
        provider_type: str,
        config: Dict[str, Any],
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Discover available sheets from a provider
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            source_id: Optional source ID (for reference)
            
        Returns:
            Dictionary with available sheets
        """
        manager = CortexSpreadsheetManager(source_id or "discover")
        sheets = manager.get_available_sheets(provider_type, config)
        
        return {
            "tables": [
                {
                    "name": sheet.name,
                    "row_count": sheet.row_count,
                    "columns": sheet.columns,
                }
                for sheet in sheets
            ]
        }
    
    @staticmethod
    def preview_sheet(
        provider_type: str,
        config: Dict[str, Any],
        sheet_name: str,
        limit: int = 100,
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Preview data from a sheet
        
        Args:
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            sheet_name: Name of the sheet to preview
            limit: Maximum rows to return
            source_id: Optional source ID
            
        Returns:
            Preview data
        """
        manager = CortexSpreadsheetManager(source_id or "preview")
        return manager.preview_sheet(provider_type, config, sheet_name, limit)
    
    @staticmethod
    def create_data_source(
        source_id: str,
        provider_type: str,
        config: Dict[str, Any],
        selected_sheets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a data source from spreadsheet sheets
        
        Args:
            source_id: Unique identifier for the data source
            provider_type: "csv" or "gsheets"
            config: Provider-specific configuration
            selected_sheets: Which sheets to import (None = all)
            
        Returns:
            Updated config with SQLite path and metadata
        """
        manager = CortexSpreadsheetManager(source_id)
        
        try:
            updated_config = manager.create_data_source(
                provider_type,
                config,
                selected_sheets,
            )
            
            return {
                "success": True,
                "config": updated_config,
                "sqlite_path": updated_config.get("sqlite_path"),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @staticmethod
    def refresh_data_source(
        source_id: str,
        provider_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Refresh a data source
        
        Args:
            source_id: Unique identifier for the data source
            provider_type: "csv" or "gsheets"
            config: Data source configuration
            
        Returns:
            Refresh results
        """
        manager = CortexSpreadsheetManager(source_id)
        
        try:
            result = manager.refresh_data_source(provider_type, config)
            
            return {
                "success": True,
                "refreshed_tables": result["refreshed_tables"],
                "unchanged_tables": result["unchanged_tables"],
                "updated_config": result["updated_config"],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
