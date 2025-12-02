from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.order_sequences import SemanticOrderSequence

from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.cache import CachePreference


class MetricResponse(BaseModel):
    """Response schema for metric data"""
    id: UUID
    environment_id: UUID
    data_model_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    title: Optional[str]
    # Query definition
    query: Optional[str]
    table_name: Optional[str]
    data_source_id: Optional[UUID]
    limit: Optional[int]
    grouped: Optional[bool]
    ordered: Optional[bool]
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    order: Optional[List[SemanticOrderSequence]] = None
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    version: int
    public: bool
    refresh: Optional[RefreshPolicy] = None
    cache: Optional[CachePreference] = None
    meta: Optional[Dict[str, Any]]
    is_valid: bool
    validation_errors: Optional[List[str]]
    compiled_query: Optional[str]
    data_model_name: Optional[str] = None  # Include parent model name
    created_at: datetime
    updated_at: datetime


class MetricListResponse(BaseModel):
    """Response schema for listing metrics"""
    metrics: List[MetricResponse]
    total_count: int
    page: int
    page_size: int


class MetricExecutionResponse(BaseModel):
    """Response schema for metric execution results"""
    success: bool
    # Execution stats, query info, etc.
    metadata: Dict[str, Any]  
    data: Optional[List[Dict[str, Any]]]
    errors: Optional[List[str]]


class MetricValidationResponse(BaseModel):
    """Response schema for metric validation"""
    is_valid: bool
    errors: Optional[List[str]]
    warnings: Optional[List[str]]
    compiled_query: Optional[str]


class MetricVersionResponse(BaseModel):
    """Response schema for metric version data"""
    id: UUID
    metric_id: UUID
    version_number: int
    snapshot_data: Dict[str, Any]
    description: Optional[str]
    created_by: Optional[UUID]
    tags: Optional[List[str]]
    created_at: datetime


class MetricVersionListResponse(BaseModel):
    """Response schema for listing metric versions"""
    versions: List[MetricVersionResponse]
    total_count: int 


class MetricRecommendationsResponse(BaseModel):
    """Response schema for metric recommendations"""
    metrics: List[MetricResponse]
    total_count: int
    metadata: Optional[Dict[str, Any]] = None 