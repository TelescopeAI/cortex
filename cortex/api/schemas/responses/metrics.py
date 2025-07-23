from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.semantics.refresh_keys import RefreshKey
from cortex.core.semantics.parameters import ParameterDefinition


class MetricResponse(BaseModel):
    """Response schema for metric data"""
    id: UUID
    data_model_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    title: Optional[str]
    query: Optional[str]
    table_name: Optional[str]
    data_source: Optional[str]
    measures: Optional[List[Dict[str, Any]]]  # Simplified as dict for now
    dimensions: Optional[List[Dict[str, Any]]]  # Simplified as dict for now
    joins: Optional[List[Dict[str, Any]]]  # Simplified as dict for now
    aggregations: Optional[List[Dict[str, Any]]]  # Simplified as dict for now
    output_formats: Optional[List[Dict[str, Any]]]  # Simplified as dict for now
    parameters: Optional[Dict[str, Any]]  # Simplified as dict for now
    model_version: int
    public: bool
    refresh_key: Optional[Dict[str, Any]]  # Simplified as dict for now
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
    data: Optional[List[Dict[str, Any]]]
    metadata: Dict[str, Any]  # Execution stats, query info, etc.
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