from typing import Optional
from uuid import UUID
from pydantic import Field, model_validator

from cortex.core.types.databases import DataSourceCatalog, DataSourceTypes
from cortex.core.types.telescope import TSModel


class DataSourceCreateRequest(TSModel):
    environment_id: UUID
    name: str
    alias: str
    description: Optional[str] = None
    source_catalog: DataSourceCatalog
    source_type: DataSourceTypes
    config: dict


class DataSourceUpdateRequest(TSModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


class DataSourceRebuildRequest(TSModel):
    """Request to rebuild a spreadsheet data source from its original file"""
    clear_cache: bool = Field(
        default=True,
        description="Clear cached SQLite file before rebuilding"
    )


class DataSourceQueryRequest(TSModel):
    """Request to run a direct query against a data source"""
    environment_id: UUID
    table: Optional[str] = None
    statement: Optional[str] = None
    limit: Optional[int] = Field(default=None, description="Row limit for table queries. None returns all rows. Ignored for statement queries.")
    offset: Optional[int] = Field(default=0, description="Row offset for table queries. Ignored for statement queries.")

    @model_validator(mode="after")
    def validate_table_or_statement(self):
        if self.table and self.statement:
            raise ValueError("Provide either 'table' or 'statement', not both")
        if not self.table and not self.statement:
            raise ValueError("Either 'table' or 'statement' must be provided")
        return self