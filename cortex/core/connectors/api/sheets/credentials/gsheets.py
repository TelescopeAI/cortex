from typing import Optional, List, Dict, Any
from pydantic import Field
from cortex.core.connectors.api.sheets.credentials.base import CortexSpreadsheetCredentials


class CortexGoogleSheetsCredentials(CortexSpreadsheetCredentials):
    """Credentials for Google Sheets access"""
    
    spreadsheet_id: str = Field(..., description="Google Sheets ID from URL")
    service_account_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Service account credentials JSON"
    )
    access_token: Optional[str] = Field(
        default=None,
        description="OAuth access token (alternative to service account)"
    )
    selected_sheets: Optional[List[str]] = Field(
        default=None,
        description="User-selected sheets to import (None = all available)"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert credentials to dictionary for storage"""
        return {
            "spreadsheet_id": self.spreadsheet_id,
            "service_account_json": self.service_account_json,
            "access_token": self.access_token,
            "selected_sheets": self.selected_sheets,
        }
