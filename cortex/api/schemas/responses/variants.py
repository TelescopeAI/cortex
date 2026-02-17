from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime

from cortex.core.semantics.metrics.metric import MetricRef
from cortex.core.semantics.metrics.overrides import MetricOverrides, IncludedComponents
from cortex.core.semantics.derivations import DerivedEntity
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.types.telescope import TSModel


class MetricVariantResponse(TSModel):
    """Response schema for variant data"""
    id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]

    # Environment/DataModel/DataSource binding
    environment_id: UUID
    data_model_id: UUID
    data_source_id: Optional[UUID]
    source_id: UUID

    # Variant definition (the recipe)
    source: MetricRef
    overrides: Optional[MetricOverrides]
    include: Optional[IncludedComponents]
    derivations: Optional[List[DerivedEntity]]
    combine: Optional[List[MetricRef]]
    composition: Optional[List[Dict[str, Any]]]  # CompositionSource as dict

    # Variant's own settings
    version: int
    public: bool
    cache: Optional[CachePreference]
    refresh: Optional[RefreshPolicy]
    parameters: Optional[Dict[str, ParameterDefinition]]
    meta: Optional[Dict[str, Any]]

    # Validation and compilation
    is_valid: bool
    validation_errors: Optional[List[str]]
    compiled_query: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Optional computed fields
    source_metric_name: Optional[str] = None

    class Config:
        from_attributes = True


class MetricVariantListResponse(TSModel):
    """Response schema for listing variants"""
    variants: List[MetricVariantResponse]
    total_count: int
    limit: Optional[int] = None
    offset: Optional[int] = None


class MetricVariantExecutionResponse(TSModel):
    """Response schema for variant execution results"""
    success: bool
    metadata: Dict[str, Any]
    data: Optional[List[Dict[str, Any]]]
    errors: Optional[List[str]]
