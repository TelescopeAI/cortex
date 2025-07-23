from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from cortex.core.types.databases import DataSourceCatalog, DataSourceTypes


class DataSourceCreateRequest(BaseModel):
    environment_id: UUID
    name: str
    alias: str
    description: Optional[str] = None
    source_catalog: DataSourceCatalog
    source_type: DataSourceTypes
    config: dict


class DataSourceUpdateRequest(BaseModel):
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None