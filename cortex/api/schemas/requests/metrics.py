from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.order_sequences import SemanticOrderSequence
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.semantics.metrics.modifiers import MetricModifiers


class MetricCreateRequest(BaseModel):
    """Request schema for creating a new metric"""
    data_model_id: UUID
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None
    table_name: Optional[str] = None
    data_source_id: Optional[UUID] = None
    limit: Optional[int] = None
    grouped: Optional[bool] = Field(default=True, description="Whether to apply GROUP BY when dimensions are present")
    ordered: Optional[bool] = Field(default=True, description="Whether to apply ORDER BY for sorting results")
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    order: Optional[List[SemanticOrderSequence]] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    extends: Optional[UUID] = None
    public: Optional[bool] = True
    refresh: Optional[RefreshPolicy] = None
    cache: Optional[CachePreference] = None
    meta: Optional[Dict[str, Any]] = None


class MetricUpdateRequest(BaseModel):
    """Request schema for updating an existing metric"""
    environment_id: UUID = Field(..., description="Environment ID for the metric")
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None
    table_name: Optional[str] = None
    data_source_id: Optional[UUID] = None
    limit: Optional[int] = None
    grouped: Optional[bool] = None
    ordered: Optional[bool] = None
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    order: Optional[List[SemanticOrderSequence]] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    extends: Optional[UUID] = None
    public: Optional[bool] = None
    refresh: Optional[RefreshPolicy] = None
    cache: Optional[CachePreference] = None
    meta: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(use_enum_values=True)


class MetricExecutionRequest(BaseModel):
    """Request schema for executing a metric"""
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    context_id: Optional[str] = None
    grouped: Optional[bool] = Field(default=True, description="Whether to apply GROUP BY when dimensions are present")
    ordered: Optional[bool] = Field(default=True, description="Whether to apply ORDER BY for sorting results")
    cache: Optional[CachePreference] = None
    modifiers: Optional[MetricModifiers] = None
    preview: Optional[bool] = Field(default=False, description="If true, generate and return query without executing or saving to DB")


class MetricCloneRequest(BaseModel):
    """Request schema for cloning a metric to another data model"""
    target_data_model_id: UUID
    new_name: Optional[str] = None


class MetricVersionCreateRequest(BaseModel):
    """Request schema for creating a metric version"""
    description: Optional[str] = None
    tags: Optional[List[str]] = None 


class MetricRecommendationsRequest(BaseModel):
    """
    Request schema for generating metric recommendations.
    Optional filters allow callers to scope tables/columns, restrict metric
    templates, and control time windows/grains for temporal outputs.
    """
    environment_id: UUID
    data_source_id: UUID
    data_model_id: UUID
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    include_columns: Optional[List[str]] = None
    exclude_columns: Optional[List[str]] = None
    metric_types: Optional[List[str]] = None
    time_windows: Optional[List[int]] = None
    grains: Optional[List[str]] = None