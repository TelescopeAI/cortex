"""
Database models for metric variants.

This module defines ORM models for metric variants and their version history.
Variants are modification recipes that reference a source metric and compile to full SemanticMetrics.
"""

from uuid import uuid4
from datetime import datetime

import pytz
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from cortex.core.data.db.models import BaseDBModel
from cortex.core.types.databases import DatabaseTypeResolver


class MetricVariantORM(BaseDBModel):
    """
    Database model for metric variants.
    Variants are modification recipes that reference a source metric.
    """
    __tablename__ = "metric_variants"

    # Primary key
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Environment/DataModel/DataSource binding (must match source metric)
    environment_id = mapped_column(UUID(as_uuid=True), ForeignKey('environments.id'), nullable=False, index=True)
    data_model_id = mapped_column(UUID(as_uuid=True), ForeignKey('data_models.id'), nullable=False, index=True)
    data_source_id = mapped_column(UUID(as_uuid=True), ForeignKey('data_sources.id'), nullable=True, index=True)

    # Source metric reference with CASCADE DELETE
    source_id = mapped_column(UUID(as_uuid=True), ForeignKey('metrics.id', ondelete='CASCADE'), nullable=False, index=True)

    # Identity
    name = mapped_column(String, nullable=False, index=True)
    alias = mapped_column(String, nullable=True, index=True)
    description = mapped_column(Text, nullable=True)

    # Variant definition (the recipe)
    source = mapped_column(DatabaseTypeResolver.json_type(), nullable=False)  # MetricRef (stores alias, join_on)
    overrides = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # MetricOverrides
    include = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # IncludedComponents
    derivations = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # List[DerivedEntity]
    combine = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # List[MetricRef]
    composition = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # List[CompositionSource]

    # Variant's own settings
    version = mapped_column(Integer, default=1, nullable=False)
    public = mapped_column(Boolean, default=True, nullable=False, index=True)
    cache = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # CachePreference
    refresh = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # RefreshPolicy
    parameters = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Dict[str, ParameterDefinition]
    meta = mapped_column(DatabaseTypeResolver.json_type(), nullable=True)  # Dict[str, Any]

    # Validation and compilation (same as MetricORM)
    is_valid = mapped_column(Boolean, nullable=False, default=False, index=True)
    validation_errors = mapped_column(DatabaseTypeResolver.array_type(), nullable=True, default=list)
    compiled_query = mapped_column(Text, nullable=True)  # Generated SQL - cached to avoid recompiling

    # Timestamps
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(pytz.UTC), index=True)
    updated_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC))

    # Relationships (without back_populates for now - will be added in Phase 6)
    environment = relationship("WorkspaceEnvironmentORM")
    data_model = relationship("DataModelORM")
    data_source = relationship("DataSourceORM")
    source_metric = relationship("MetricORM", foreign_keys=[source_id])  # Source metric (CASCADE DELETE)
    versions = relationship("MetricVariantVersionORM", back_populates="variant", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('ix_metric_variants_env_model', 'environment_id', 'data_model_id'),
        Index('ix_metric_variants_name_model', 'name', 'data_model_id'),
    )


class MetricVariantVersionORM(BaseDBModel):
    """
    Database model for metric variant versions.
    Stores complete snapshots of variant definitions for audit and rollback.
    """
    __tablename__ = "metric_variant_versions"

    # Primary key
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign key to variant
    variant_id = mapped_column(UUID(as_uuid=True), ForeignKey('metric_variants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Version metadata
    version_number = mapped_column(Integer, nullable=False, index=True)
    snapshot_data = mapped_column(DatabaseTypeResolver.json_type(), nullable=False)  # Complete SemanticMetricVariant as JSON
    description = mapped_column(Text, nullable=True)
    created_by = mapped_column(UUID(as_uuid=True), nullable=True)
    tags = mapped_column(DatabaseTypeResolver.array_type(), nullable=True)

    # Timestamp
    created_at = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(pytz.UTC), index=True)

    # Relationship
    variant = relationship("MetricVariantORM", back_populates="versions")

    # Indexes
    __table_args__ = (
        Index('ix_metric_variant_versions_variant_version', 'variant_id', 'version_number'),
    )
