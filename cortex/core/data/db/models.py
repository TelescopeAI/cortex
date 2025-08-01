from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy import String, DateTime, UUID, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey

from cortex.core.stores.sqlalchemy import BaseDBModel


class DataModelORM(BaseDBModel):
    __tablename__ = "data_models"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    data_source_id = mapped_column(UUID, ForeignKey("data_sources.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    alias = mapped_column(String, nullable=True, index=True)
    description = mapped_column(Text, nullable=True)
    
    # Versioning support
    version = mapped_column(Integer, nullable=False, default=1)
    is_active = mapped_column(Boolean, nullable=False, default=True, index=True)
    parent_version_id = mapped_column(UUID, ForeignKey("data_models.id"), nullable=True)
    
    # Custom configuration dictionary for model-level settings
    config = mapped_column(JSONB, nullable=False, default={})
    
    # Validation state
    is_valid = mapped_column(Boolean, nullable=False, default=False, index=True)
    validation_errors = mapped_column(ARRAY(String), nullable=True)
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))


class ModelVersionORM(BaseDBModel):
    __tablename__ = "model_versions"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    data_model_id = mapped_column(UUID, ForeignKey("data_models.id"), nullable=False, index=True)
    version_number = mapped_column(Integer, nullable=False, index=True)
    
    # Complete semantic model snapshot
    semantic_model = mapped_column(JSONB, nullable=False, default={})
    
    # Validation state at time of version creation
    is_valid = mapped_column(Boolean, nullable=False, default=False)
    validation_errors = mapped_column(ARRAY(String), nullable=True)
    compiled_queries = mapped_column(JSONB, nullable=True)  # metric_alias -> query
    
    # Version metadata
    description = mapped_column(Text, nullable=True)  # Description of changes in this version
    created_by = mapped_column(UUID, nullable=True)  # User who created this version
    tags = mapped_column(ARRAY(String), nullable=True)  # Tags for categorizing versions
    
    # Legacy config (for backward compatibility)
    config = mapped_column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)


class MetricORM(BaseDBModel):
    __tablename__ = "metrics"
    
    id = mapped_column(UUID, primary_key=True, index=True)
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
    
    # Metric components (stored as JSON)
    measures = mapped_column(JSONB, nullable=True)  # Array of SemanticMeasure objects
    dimensions = mapped_column(JSONB, nullable=True)  # Array of SemanticDimension objects
    joins = mapped_column(JSONB, nullable=True)  # Array of SemanticJoin objects
    aggregations = mapped_column(JSONB, nullable=True)  # Array of SemanticAggregation objects
    filters = mapped_column(JSONB, nullable=True)  # Array of SemanticFilter objects
    output_formats = mapped_column(JSONB, nullable=True)  # Array of OutputFormat objects
    
    # Configuration
    parameters = mapped_column(JSONB, nullable=True)  # Parameter definitions
    model_version = mapped_column(Integer, nullable=False, default=1)
    extends = mapped_column(UUID, ForeignKey("metrics.id"), nullable=True, index=True)  # Parent metric for inheritance
    public = mapped_column(Boolean, nullable=False, default=True, index=True)
    refresh_key = mapped_column(JSONB, nullable=True)  # RefreshKey object
    meta = mapped_column(JSONB, nullable=True)  # Custom metadata
    
    # Validation and compilation
    is_valid = mapped_column(Boolean, nullable=False, default=False, index=True)
    validation_errors = mapped_column(ARRAY(String), nullable=True)
    compiled_query = mapped_column(Text, nullable=True)  # Generated SQL
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))


class MetricVersionORM(BaseDBModel):
    __tablename__ = "metric_versions"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    metric_id = mapped_column(UUID, ForeignKey("metrics.id"), nullable=False, index=True)
    version_number = mapped_column(Integer, nullable=False, index=True)
    
    # Complete metric snapshot
    snapshot_data = mapped_column(JSONB, nullable=False)  # Complete metric definition snapshot
    description = mapped_column(Text, nullable=True)  # Version change description
    created_by = mapped_column(UUID, nullable=True)  # User who created this version
    tags = mapped_column(ARRAY(String), nullable=True)  # Tags for categorizing versions
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), index=True)