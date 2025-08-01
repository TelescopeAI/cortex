from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.semantics.refresh_keys import RefreshKey
from cortex.core.semantics.parameters import ParameterDefinition


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
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    output_formats: Optional[List[OutputFormat]] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    extends: Optional[UUID] = None
    public: Optional[bool] = True
    refresh_key: Optional[RefreshKey] = None
    meta: Optional[Dict[str, Any]] = None


class MetricUpdateRequest(BaseModel):
    """Request schema for updating an existing metric"""
    name: Optional[str] = None
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None
    table_name: Optional[str] = None
    data_source_id: Optional[UUID] = None
    limit: Optional[int] = None
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    output_formats: Optional[List[OutputFormat]] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    extends: Optional[UUID] = None
    public: Optional[bool] = None
    refresh_key: Optional[RefreshKey] = None
    meta: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(use_enum_values=True)




class MetricExecutionRequest(BaseModel):
    """Request schema for executing a metric"""
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class MetricCloneRequest(BaseModel):
    """Request schema for cloning a metric to another data model"""
    target_data_model_id: UUID
    new_name: Optional[str] = None


class MetricVersionCreateRequest(BaseModel):
    """Request schema for creating a metric version"""
    description: Optional[str] = None
    tags: Optional[List[str]] = None 