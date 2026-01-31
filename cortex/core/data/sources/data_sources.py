from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

import pytz
from pydantic import Field

from cortex.core.types.databases import DataSourceTypes, DataSourceCatalog
from cortex.core.types.telescope import TSModel


class DataSource(TSModel):
    id: UUID = Field(default_factory=uuid4)
    environment_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    source_catalog: DataSourceCatalog
    source_type: DataSourceTypes
    config: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


class CortexFileStorage(TSModel):
    id: UUID = Field(default_factory=uuid4)
    environment_id: UUID
    name: str
    mime_type: Optional[str] = None
    extension: str
    size: Optional[int] = None
    path: str  # Will be encrypted in DB
    hash: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
