from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

from cortex.core.types.telescope import TSModel
from pydantic import Field


class DataModelResponse(TSModel):
    """Response schema for data model operations."""
    id: UUID
    environment_id: UUID
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    version: int
    is_active: bool
    parent_version_id: Optional[UUID] = None
    config: Dict[str, Any]
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    metrics_count: int = 0
    created_at: datetime
    updated_at: datetime


class DataModelListResponse(TSModel):
    """Response schema for listing data models."""
    models: List[DataModelResponse]
    total_count: int
    page: int
    page_size: int


class ModelExecutionResponse(TSModel):
    """Response schema for metric execution."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any]


class ModelValidationResponse(TSModel):
    """Response schema for model validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_at: datetime


class QueryLogResponse(TSModel):
    """Response schema for query log entries."""
    id: UUID
    metric_alias: str
    metric_id: UUID
    data_model_id: UUID
    query: str
    parameters: Optional[Dict[str, Any]] = None
    duration: float
    row_count: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    executed_at: datetime


class QueryLogListResponse(TSModel):
    """Response schema for listing query log entries."""
    entries: List[QueryLogResponse]
    total_count: int


class ExecutionStatsResponse(TSModel):
    """Response schema for execution statistics."""
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    average_duration: float


class ModelVersionResponse(TSModel):
    """Response schema for model versions."""
    id: UUID
    data_model_id: UUID
    version_number: int
    semantic_model: Dict[str, Any]
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    compiled_queries: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    created_by: Optional[UUID] = None
    tags: Optional[List[str]] = None
    config: Dict[str, Any]
    created_at: datetime


class ModelVersionListResponse(TSModel):
    """Response schema for listing model versions."""
    versions: List[ModelVersionResponse]
    total_count: int


class MetricResponse(TSModel):
    """Response schema for individual metrics."""
    id: UUID
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    data_source_id: Optional[UUID] = None
    version: int
    public: bool
    created_at: datetime
    updated_at: datetime


class MetricListResponse(TSModel):
    """Response schema for listing metrics from a data model."""
    metrics: List[MetricResponse]
    total_count: int 