from typing import Optional
from uuid import UUID
from pydantic import Field

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