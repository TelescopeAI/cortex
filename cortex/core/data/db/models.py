from datetime import datetime
from typing import Optional
from uuid import uuid4

import pytz
from sqlalchemy import String, DateTime, UUID, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel
from cortex.core.types.databases import DatabaseTypeResolver


class DataModelORM(BaseDBModel):
    __tablename__ = "data_models"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    alias = mapped_column(String, nullable=True, index=True)
    description = mapped_column(Text, nullable=True)
    
    # Versioning support
    version = mapped_column(Integer, nullable=False, default=1)
    is_active = mapped_column(Boolean, nullable=False, default=True, index=True)
    parent_version_id = mapped_column(UUID, ForeignKey("data_models.id"), nullable=True)
    
    # Custom configuration dictionary for model-level settings
    config = mapped_column(DatabaseTypeResolver.json_type(), nullable=False, default={})
    
    # Validation state
    is_valid = mapped_column(Boolean, nullable=False, default=False, index=True)
    validation_errors = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))


class ModelVersionORM(BaseDBModel):
    __tablename__ = "model_versions"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    data_model_id = mapped_column(UUID, ForeignKey("data_models.id"), nullable=False, index=True)
    version_number = mapped_column(Integer, nullable=False, index=True)
    
    # Complete semantic model snapshot
    semantic_model = mapped_column(DatabaseTypeResolver.json_type(), nullable=False, default={})
    
    # Validation state at time of version creation
    is_valid = mapped_column(Boolean, nullable=False, default=False)
    validation_errors = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)
    compiled_queries = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # metric_alias -> query
    
    # Version metadata
    description = mapped_column(Text, nullable=True)  # Description of changes in this version
    created_by = mapped_column(UUID, nullable=True)  # User who created this version
    tags = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)  # Tags for categorizing versions
    
    # Legacy config (for backward compatibility)
    config = mapped_column(DatabaseTypeResolver.json_type(), nullable=False, default={})
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)


class MetricORM(BaseDBModel):
    __tablename__ = "metrics"
    
    # Generate UUID in application layer to satisfy NOT NULL without relying on DB defaults
    id = mapped_column(UUID, primary_key=True, index=True, default=uuid4)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    data_model_id = mapped_column(UUID, ForeignKey("data_models.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    alias = mapped_column(String, nullable=True, index=True)
    description = mapped_column(Text, nullable=True)
    title = mapped_column(String, nullable=True)
    
    # Query definition
    query = mapped_column(Text, nullable=True)  # Custom SQL query
    table_name = mapped_column(String, nullable=True)  # Source table
    data_source_id = mapped_column(UUID, ForeignKey("data_sources.id"), nullable=True, index=True)
    limit = mapped_column(Integer, nullable=True)  # Default limit for query results
    grouped = mapped_column(Boolean, nullable=True, default=True)  # Whether to apply GROUP BY when dimensions are present
    ordered = mapped_column(Boolean, nullable=True, default=True)  # Whether to apply ORDER BY for sorting results
    
    # Metric components (stored as JSON)
    measures = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticMeasure objects
    dimensions = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticDimension objects
    joins = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticJoin objects
    aggregations = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticAggregation objects
    filters = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticFilter objects
    order = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Array of SemanticOrderSequence objects
    
    # Configuration
    parameters = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Parameter definitions
    version = mapped_column(Integer, nullable=False, default=1)
    extends = mapped_column(UUID, ForeignKey("metrics.id"), nullable=True, index=True)  # Parent metric for inheritance
    public = mapped_column(Boolean, nullable=False, default=True, index=True)
    refresh = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # RefreshPolicy object
    cache = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # CachePreference object
    meta = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Custom metadata
    
    # Validation and compilation
    is_valid = mapped_column(Boolean, nullable=False, default=False, index=True)
    validation_errors = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)
    compiled_query = mapped_column(Text, nullable=True)  # Generated SQL
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))


class MetricVersionORM(BaseDBModel):
    __tablename__ = "metric_versions"
    
    id = mapped_column(UUID, primary_key=True, index=True, default=uuid4)
    metric_id = mapped_column(UUID, ForeignKey("metrics.id"), nullable=False, index=True)
    version_number = mapped_column(Integer, nullable=False, index=True)
    
    # Complete metric snapshot
    snapshot_data = mapped_column(DatabaseTypeResolver.json_type(), nullable=False)  # Complete metric definition snapshot
    description = mapped_column(Text, nullable=True)  # Version change description
    created_by = mapped_column(UUID, nullable=True)  # User who created this version
    tags = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)  # Tags for categorizing versions
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)