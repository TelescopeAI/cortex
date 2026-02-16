import io
from pathlib import Path
from typing import List, Dict, Optional
from cortex.core.connectors.api.sheets.providers.base import CortexSpreadsheetProvider
from cortex.core.connectors.api.sheets.types import (
    CortexSheetMetadata,
    CortexSheetPreview,
    CortexSpreadsheetMetadata,
    CortexCSVFileConfig,
)


class CortexCSVProvider(CortexSpreadsheetProvider):
    """Provider for CSV files"""
    
    def __init__(self, files: List[CortexCSVFileConfig], source_id: str, storage_backend=None):
        """
        Initialize CSV provider
        
        Args:
            files: List of CSV file configurations
            source_id: Unique identifier for the data source
            storage_backend: Optional storage backend for reading remote files (GCS, S3, etc.)
        """
        self.files = files
        self.source_id = source_id
        self._sheet_data_cache = {}
        self.storage_backend = storage_backend
    
    def list_sheets(self) -> List[CortexSheetMetadata]:
        """List available CSV files as sheets"""
        sheets = []
        
        for file_config in self.files:
            try:
                # Try to read the file
                csv_data = self._read_csv_file(file_config)
                lines = csv_data.decode('utf-8').split('\n')
                
                # Parse headers
                if lines:
                    headers = lines[0].split(',') if lines[0] else []
                    row_count = len(lines) - 1  # Subtract header
                    
                    # Cache the data
                    self._sheet_data_cache[file_config.filename] = csv_data
                    
                    sheets.append(CortexSheetMetadata(
                        name=file_config.filename,
                        row_count=row_count,
                        columns=headers,
                        source_type="csv"
                    ))
            except Exception as e:
                print(f"Error reading {file_config.filename}: {e}")
                continue
        
        return sheets
    
    def preview_sheet(self, sheet_name: str, limit: int = 100) -> CortexSheetPreview:
        """Get preview of CSV file"""
        csv_data = self._read_csv_file_by_name(sheet_name)
        
        lines = csv_data.decode('utf-8').split('\n')
        
        if not lines:
            return CortexSheetPreview(columns=[], rows=[], total_rows=0)
        
        # Parse headers
        headers = lines[0].split(',') if lines[0] else []
        
        # Get data rows
        data_rows = []
        for line in lines[1:limit + 1]:
            if line.strip():
                row = line.split(',')
                data_rows.append(row)
        
        total_rows = len(lines) - 1  # Subtract header
        
        return CortexSheetPreview(
            columns=headers,
            rows=data_rows,
            total_rows=total_rows
        )
    
    def download_sheet(self, sheet_name: str) -> bytes:
        """Download a CSV file"""
        return self._read_csv_file_by_name(sheet_name)
    
    def download_selected(self, sheet_names: List[str]) -> Dict[str, bytes]:
        """Download multiple CSV files"""
        result = {}
        
        for sheet_name in sheet_names:
            try:
                result[sheet_name] = self._read_csv_file_by_name(sheet_name)
            except Exception as e:
                print(f"Error downloading {sheet_name}: {e}")
                continue
        
        return result
    
    def get_metadata(self) -> CortexSpreadsheetMetadata:
        """Get metadata about the CSV files"""
        sheets = self.list_sheets()
        
        return CortexSpreadsheetMetadata(
            source_id=self.source_id,
            sheets=sheets,
            source_type="csv"
        )
    
    def _read_csv_file_by_name(self, filename: str) -> bytes:
        """Read a CSV file by name"""
        # Check cache first
        if filename in self._sheet_data_cache:
            return self._sheet_data_cache[filename]
        
        # Find the file config
        file_config = None
        for fc in self.files:
            if fc.filename == filename:
                file_config = fc
                break
        
        if not file_config:
            raise FileNotFoundError(f"File not found: {filename}")
        
        return self._read_csv_file(file_config)
    
    def _read_csv_file(self, file_config: CortexCSVFileConfig) -> bytes:
        """Read a CSV file and return as bytes"""
        file_path = file_config.file_path
        
        if not file_path:
            raise ValueError("File path is required")
        
        # Check if it's a GCS or S3 path (starts with gs:// or s3://)
        if file_path.startswith('gs://') or file_path.startswith('s3://'):
            # Use storage backend to read remote file
            if not self.storage_backend:
                raise ValueError(f"Storage backend required to read remote file: {file_path}")

            # Use full path from database directly (no parsing needed!)
            # File paths are stored with full hierarchical structure in the database
            if file_path.startswith('gs://'):
                # Extract blob path from GCS URI
                # Format: gs://bucket/blob_path
                blob_path = file_path.replace(f'gs://{self.storage_backend.bucket.name}/', '')

                # Use storage backend's load_file method with blob_path parameter
                file_data = self.storage_backend.load_file(blob_path=blob_path)

                if file_data is None:
                    raise FileNotFoundError(f"GCS file not found: {file_path}")

                return file_data
            elif file_path.startswith('s3://'):
                # S3 support can be added here similarly
                raise NotImplementedError("S3 storage not yet implemented")
        
        # Local file handling
        if file_config.source_type == "file" and file_path:
            # Read from local file
            with open(file_path, 'rb') as f:
                return f.read()
        elif file_config.source_type == "upload" and file_path:
            # File uploaded to inputs directory
            with open(file_path, 'rb') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported CSV source: {file_config.source_type}")
