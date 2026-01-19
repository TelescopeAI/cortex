from enum import Enum
from typing import Optional, List
from pydantic import Field
from cortex.core.types.telescope import TSModel


class CortexSheetsStorageType(str, Enum):
    """Storage backend types for spreadsheet data"""
    LOCAL = "local"
    GCS = "gcs"
    S3 = "s3"


class CortexSheetMetadata(TSModel):
    """Metadata about a sheet/table available for import"""
    name: str
    row_count: int
    columns: List[str]
    source_type: Optional[str] = None


class CortexSheetPreview(TSModel):
    """Preview data for a sheet"""
    columns: List[str]
    rows: List[List[Optional[str]]]
    total_rows: int


class CortexSpreadsheetMetadata(TSModel):
    """Metadata about an entire spreadsheet"""
    source_id: str
    sheets: List[CortexSheetMetadata]
    last_modified: Optional[str] = None
    source_type: str  # "gsheets", "csv", etc.


class CortexCSVFileConfig(TSModel):
    """Configuration for a CSV file"""
    filename: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    source_type: str = Field(default="file")  # "file", "url", "upload"
