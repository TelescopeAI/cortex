from abc import ABC, abstractmethod
from typing import List, Dict
from cortex.core.connectors.api.sheets.types import (
    CortexSheetMetadata,
    CortexSheetPreview,
    CortexSpreadsheetMetadata,
)


class CortexSpreadsheetProvider(ABC):
    """Abstract base class for spreadsheet providers"""
    
    @abstractmethod
    def list_sheets(self) -> List[CortexSheetMetadata]:
        """
        List all available sheets with metadata
        
        Returns:
            List of sheet metadata
        """
        pass
    
    @abstractmethod
    def preview_sheet(self, sheet_name: str, limit: int = 100) -> CortexSheetPreview:
        """
        Get a preview of a sheet's data
        
        Args:
            sheet_name: Name of the sheet to preview
            limit: Maximum number of rows to return
            
        Returns:
            Preview data with columns and rows
        """
        pass
    
    @abstractmethod
    def download_sheet(self, sheet_name: str) -> bytes:
        """
        Download a sheet as CSV data
        
        Args:
            sheet_name: Name of the sheet to download
            
        Returns:
            CSV data as bytes
        """
        pass
    
    @abstractmethod
    def download_selected(self, sheet_names: List[str]) -> Dict[str, bytes]:
        """
        Download multiple sheets as CSV data
        
        Args:
            sheet_names: List of sheet names to download
            
        Returns:
            Dict mapping sheet names to CSV data as bytes
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> CortexSpreadsheetMetadata:
        """
        Get metadata about the entire spreadsheet
        
        Returns:
            Spreadsheet metadata including all sheets
        """
        pass
