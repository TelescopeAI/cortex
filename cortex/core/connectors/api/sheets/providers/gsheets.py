import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.auth import default as google_auth_default
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from cortex.core.connectors.api.sheets.providers.base import CortexSpreadsheetProvider
from cortex.core.connectors.api.sheets.types import (
    CortexSheetMetadata,
    CortexSheetPreview,
    CortexSpreadsheetMetadata,
)


class CortexGoogleSheetsProvider(CortexSpreadsheetProvider):
    """Provider for Google Sheets"""
    
    def __init__(
        self,
        spreadsheet_id: str,
        service_account_json: Optional[Dict] = None,
        access_token: Optional[str] = None,
        source_id: Optional[str] = None,
    ):
        """
        Initialize Google Sheets provider
        
        Args:
            spreadsheet_id: Google Sheets ID from URL
            service_account_json: Service account credentials JSON
            access_token: OAuth access token (alternative to service account)
            source_id: Unique identifier for the data source
        """
        self.spreadsheet_id = spreadsheet_id
        self.service_account_json = service_account_json
        self.access_token = access_token
        self.source_id = source_id or spreadsheet_id
        
        # Initialize credentials and client
        self._init_client()
    
    def _init_client(self):
        """Initialize Google Sheets API client"""
        try:
            if self.service_account_json:
                # Use service account credentials
                credentials = ServiceAccountCredentials.from_service_account_info(
                    self.service_account_json,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                self.sheets_client = build('sheets', 'v4', credentials=credentials)
            elif self.access_token:
                # Note: Using access token with build() requires special handling
                # For now, we'll use service account flow
                raise NotImplementedError("OAuth access token flow requires additional setup")
            else:
                # Try to use default credentials (local development)
                credentials, _ = google_auth_default()
                self.sheets_client = build('sheets', 'v4', credentials=credentials)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google Sheets client: {e}")
    
    def list_sheets(self) -> List[CortexSheetMetadata]:
        """List all sheets in the spreadsheet"""
        try:
            spreadsheet = self.sheets_client.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id,
                fields='sheets'
            ).execute()
            
            sheets_metadata = []
            for sheet in spreadsheet.get('sheets', []):
                sheet_name = sheet['properties']['title']
                sheet_id = sheet['properties']['sheetId']
                
                # Get data from the sheet to determine row count and columns
                try:
                    values_result = self.sheets_client.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"'{sheet_name}'",
                        majorDimension='ROWS'
                    ).execute()
                    
                    values = values_result.get('values', [])
                    
                    if values:
                        columns = values[0]  # First row is headers
                        row_count = len(values) - 1  # Subtract header row
                    else:
                        columns = []
                        row_count = 0
                    
                    sheets_metadata.append(CortexSheetMetadata(
                        name=sheet_name,
                        row_count=row_count,
                        columns=columns,
                        source_type="gsheets"
                    ))
                except Exception as e:
                    print(f"Error reading sheet {sheet_name}: {e}")
                    continue
            
            return sheets_metadata
        except Exception as e:
            raise RuntimeError(f"Failed to list sheets: {e}")
    
    def preview_sheet(self, sheet_name: str, limit: int = 100) -> CortexSheetPreview:
        """Get preview of a sheet"""
        try:
            # Get data from the sheet
            values_result = self.sheets_client.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A1:Z{limit+1}",
                majorDimension='ROWS'
            ).execute()
            
            values = values_result.get('values', [])
            
            if not values:
                return CortexSheetPreview(columns=[], rows=[], total_rows=0)
            
            # First row is headers
            columns = values[0] if values else []
            
            # Data rows
            data_rows = values[1:limit+1] if len(values) > 1 else []
            
            # Get total row count
            all_values = self.sheets_client.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'",
                majorDimension='ROWS'
            ).execute().get('values', [])
            
            total_rows = len(all_values) - 1  # Subtract header
            
            return CortexSheetPreview(
                columns=columns,
                rows=data_rows,
                total_rows=total_rows
            )
        except Exception as e:
            raise RuntimeError(f"Failed to preview sheet {sheet_name}: {e}")
    
    def download_sheet(self, sheet_name: str) -> bytes:
        """Download a sheet as CSV"""
        try:
            # Get all data from the sheet
            values_result = self.sheets_client.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'",
                majorDimension='ROWS'
            ).execute()
            
            values = values_result.get('values', [])
            
            # Convert to CSV format
            csv_buffer = io.StringIO()
            for row in values:
                # Handle missing columns by padding with empty strings
                csv_row = []
                for cell in row:
                    # Escape quotes and wrap in quotes if needed
                    if isinstance(cell, str) and (',' in cell or '"' in cell or '\n' in cell):
                        csv_row.append(f'"{cell.replace(chr(34), chr(34)+chr(34))}"')
                    else:
                        csv_row.append(str(cell))
                csv_buffer.write(','.join(csv_row) + '\n')
            
            return csv_buffer.getvalue().encode('utf-8')
        except Exception as e:
            raise RuntimeError(f"Failed to download sheet {sheet_name}: {e}")
    
    def download_selected(self, sheet_names: List[str]) -> Dict[str, bytes]:
        """Download multiple sheets"""
        result = {}
        
        for sheet_name in sheet_names:
            try:
                result[sheet_name] = self.download_sheet(sheet_name)
            except Exception as e:
                print(f"Error downloading {sheet_name}: {e}")
                continue
        
        return result
    
    def get_metadata(self) -> CortexSpreadsheetMetadata:
        """Get metadata about the spreadsheet"""
        sheets = self.list_sheets()
        
        return CortexSpreadsheetMetadata(
            source_id=self.source_id,
            sheets=sheets,
            source_type="gsheets"
        )
