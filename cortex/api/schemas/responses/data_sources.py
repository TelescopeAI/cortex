from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from cortex.core.types.databases import DataSourceTypes, DataSourceCatalog


class DataSourceResponse(BaseModel):
    id: UUID
    environment_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    source_catalog: DataSourceCatalog
    source_type: DataSourceTypes
    config: dict
    created_at: datetime
    updated_at: datetime
    