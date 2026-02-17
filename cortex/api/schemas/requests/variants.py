from typing import Optional, Dict, List, Any
from uuid import UUID
from pydantic import Field

from cortex.core.semantics.metrics.metric import MetricRef
from cortex.core.semantics.metrics.overrides import MetricOverrides, IncludedComponents
from cortex.core.semantics.derivations import DerivedEntity
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.types.telescope import TSModel


class MetricVariantCreateRequest(TSModel):
    """Request schema for creating a new metric variant"""
    environment_id: UUID = Field(..., description="Environment ID for the variant")
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


class MetricVariantUpdateRequest(TSModel):
    """Request schema for updating an existing metric variant"""
    environment_id: UUID = Field(..., description="Environment ID for the variant")
    name: Optional[str] = Field(None, description="Unique identifier name for this variant")
    alias: Optional[str] = Field(None, description="Optional alias for CTE context")
    description: Optional[str] = Field(None, description="Human-readable explanation of this variant")

    # Variant definition (the recipe)
    source: Optional[MetricRef] = Field(None, description="The base metric to inherit from and modify")
    overrides: Optional[MetricOverrides] = Field(
        None,
        description="Component overrides (add/replace/exclude) and scalar field overrides"
    )
    include: Optional[IncludedComponents] = Field(
        None,
        description="Whitelist of components to inherit from source (if not specified, all are inherited)"
    )
    derivations: Optional[List[DerivedEntity]] = Field(
        None,
        description="Derived entities (currently measures, future: dimensions)"
    )
    combine: Optional[List[MetricRef]] = Field(
        None,
        description="Additional metrics to join via CTEs for multi-source composition"
    )

    # Variant's own settings
    public: Optional[bool] = Field(None, description="Whether this variant is publicly accessible")
    cache: Optional[CachePreference] = Field(
        None,
        description="Cache preferences for this variant"
    )
    refresh: Optional[RefreshPolicy] = Field(
        None,
        description="Refresh policy for this variant"
    )
    parameters: Optional[Dict[str, ParameterDefinition]] = Field(
        None,
        description="Runtime parameters for dynamic query generation"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata for this variant"
    )


class MetricVariantExecutionRequest(TSModel):
    """Request schema for executing a variant"""
    environment_id: UUID = Field(..., description="Environment ID for execution")
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    context_id: Optional[str] = None
    grouped: Optional[bool] = Field(default=True, description="Whether to apply GROUP BY when dimensions are present")
    ordered: Optional[bool] = Field(default=True, description="Whether to apply ORDER BY for sorting results")
    cache: Optional[CachePreference] = None
    preview: Optional[bool] = Field(default=False, description="If true, generate and return query without executing")


class MetricVariantCloneRequest(TSModel):
    """Request schema for cloning a variant"""
    name: str = Field(..., description="Name for the cloned variant")
    alias: Optional[str] = Field(None, description="Optional alias for the cloned variant")
    description: Optional[str] = Field(None, description="Optional description for the cloned variant")
