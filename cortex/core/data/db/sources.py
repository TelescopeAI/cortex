from datetime import datetime
import pytz
from sqlalchemy import String, DateTime, UUID, Integer, Text
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey
from uuid import uuid4

from cortex.core.storage.sqlalchemy import BaseDBModel
from cortex.core.types.databases import DatabaseTypeResolver


class DataSourceORM(BaseDBModel):
    __tablename__ = "data_sources"
    id = mapped_column(UUID, primary_key=True, index=True)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    alias = mapped_column(String, nullable=True)
    description = mapped_column(String, nullable=True)
    source_catalog = mapped_column(String, nullable=False)  # Will store enum value
    source_type = mapped_column(String, nullable=False)     # Will store enum value
    config = mapped_column(DatabaseTypeResolver.json_type(), nullable=False)
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))


class CortexFileStorageORM(BaseDBModel):
    __tablename__ = "file_storage"
    
    id = mapped_column(UUID, primary_key=True, index=True, default=uuid4)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    mime_type = mapped_column(String, nullable=True)
    extension = mapped_column(String, nullable=False)
    size = mapped_column(Integer, nullable=True)
    path = mapped_column(Text, nullable=False)  # Encrypted with AES
    hash = mapped_column(String, nullable=True)  # SHA256
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))
    