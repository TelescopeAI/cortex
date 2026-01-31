from typing import Optional, List, Dict, Any, Literal
from pydantic import Field
from cortex.core.connectors.api.sheets.credentials.base import CortexSpreadsheetCredentials
from cortex.core.connectors.api.sheets.types import CortexCSVFileConfig


class CortexCSVCredentials(CortexSpreadsheetCredentials):
    """Credentials for CSV file upload/import"""
    
    source_type: Literal["file", "upload"] = Field(
        default="file",
        description="Type of CSV source"
    )
    files: List[CortexCSVFileConfig] = Field(
        default_factory=list,
        description="List of CSV files to import"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert credentials to dictionary for storage"""
        return {
            "source_type": self.source_type,
            "files": [f.model_dump() for f in self.files],
        }
