from typing import Optional, Dict, List, Any
from uuid import UUID
from pydantic import Field, model_validator

from cortex.core.semantics.metrics.metric import MetricRef
from cortex.core.semantics.metrics.overrides import MetricOverrides, IncludedComponents
from cortex.core.semantics.derivations import DerivedEntity
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.types.telescope import TSModel


class MetricVariantBaseRequest(TSModel):
    """Base variant definition fields (no environment_id)"""
    name: str = Field(..., description="Unique identifier name for this variant")
    alias: Optional[str] = Field(default=None, description="Optional alias for CTE context")
    description: Optional[str] = Field(default=None, description="Human-readable explanation of this variant")

    # Variant definition (the recipe)
    source: MetricRef = Field(..., description="REQUIRED: The base metric to inherit from and modify")
    overrides: Optional[MetricOverrides] = Field(
        default=None,
        description="Component overrides (add/replace/exclude) and scalar field overrides"
    )
    include: Optional[IncludedComponents] = Field(
        default=None,
        description="Whitelist of components to inherit from source (if not specified, all are inherited)"
    )
    derivations: Optional[List[DerivedEntity]] = Field(
        default=None,
        description="Derived entities (currently measures, future: dimensions)"
    )
    combine: Optional[List[MetricRef]] = Field(
        default=None,
        description="Additional metrics to join via CTEs for multi-source composition"
    )

    # Variant's own settings
    public: Optional[bool] = Field(default=True, description="Whether this variant is publicly accessible")
    cache: Optional[CachePreference] = Field(
        default=None,
        description="Cache preferences for this variant"
    )
    refresh: Optional[RefreshPolicy] = Field(
        default=None,
        description="Refresh policy for this variant"
    )
    parameters: Optional[Dict[str, ParameterDefinition]] = Field(
        default=None,
        description="Runtime parameters for dynamic query generation"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for this variant"
    )


class MetricVariantCreateRequest(MetricVariantBaseRequest):
    """Request schema for creating a new metric variant"""
    environment_id: UUID = Field(..., description="Environment ID for the variant")


class MetricVariantUpdateRequest(MetricVariantBaseRequest):
    """Request schema for updating an existing metric variant"""
    environment_id: UUID = Field(..., description="Environment ID for the variant")
    # Override required fields to be optional for partial updates
    name: Optional[str] = Field(None, description="Unique identifier name for this variant")
    source: Optional[MetricRef] = Field(None, description="The base metric to inherit from and modify")


class MetricVariantExecutionRequest(TSModel):
    """Request schema for executing a variant by ID or inline definition"""
    environment_id: UUID = Field(..., description="Environment ID for execution")

    # Either variant_id OR variant must be provided (not both)
    variant_id: Optional[UUID] = Field(default=None, description="ID of a saved variant to execute")
    variant: Optional[MetricVariantBaseRequest] = Field(
        default=None,
        description="Inline variant definition for preview without saving"
    )

    # Execution parameters
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    context_id: Optional[str] = None
    grouped: Optional[bool] = Field(default=True, description="Whether to apply GROUP BY when dimensions are present")
    ordered: Optional[bool] = Field(default=True, description="Whether to apply ORDER BY for sorting results")
    cache: Optional[CachePreference] = None
    preview: Optional[bool] = Field(default=False, description="If true, generate and return query without executing")

    @model_validator(mode='after')
    def validate_variant_or_id(self):
        if self.variant_id is None and self.variant is None:
            raise ValueError("Either 'variant_id' or 'variant' must be provided")
        if self.variant_id is not None and self.variant is not None:
            raise ValueError("Only one of 'variant_id' or 'variant' can be provided, not both")
        return self


class MetricVariantCloneRequest(TSModel):
    """Request schema for cloning a variant"""
    name: str = Field(..., description="Name for the cloned variant")
    alias: Optional[str] = Field(None, description="Optional alias for the cloned variant")
    description: Optional[str] = Field(None, description="Optional description for the cloned variant")
