"""
Variant model for composable metrics system.

This module defines metric variants - modification recipes that compile to full SemanticMetrics.
Variants inherit from a source metric and can modify it through overrides, inclusions, exclusions,
derivations, and multi-source composition.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

import pytz
from pydantic import Field, ConfigDict

from cortex.core.types.telescope import TSModel
from cortex.core.semantics.metrics.metric import MetricRef
from cortex.core.semantics.metrics.overrides import MetricOverrides, IncludedComponents
from cortex.core.semantics.derivations import DerivedEntity
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.parameters import ParameterDefinition


class SemanticMetricVariant(TSModel):
    """
    A modification recipe that compiles to a SemanticMetric.

    Variants define how to modify a source metric through:
    - source: The base metric to inherit from (REQUIRED)
    - include: Whitelist of components to inherit
    - overrides: Add/replace/exclude operations on components
    - derivations: Additional derived entities (measures, future: dimensions)
    - combine: Additional metrics to join via CTEs

    Key design points:
    - Separate from SemanticMetric (no inheritance) for clean autocomplete
    - No table_name, measures, dimensions - these come from resolution
    - No environment_id, data_model_id - inherited from source
    - Compiled to SemanticMetric via the compiler module
    """
    model_config = ConfigDict(from_attributes=True)

    # Identity (variant's own)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Unique identifier name for this variant")
    alias: Optional[str] = Field(
        default=None,
        description="Optional alias for CTE context"
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of this variant"
    )

    # Variant definition (the recipe)
    source: MetricRef = Field(
        ...,
        description="REQUIRED: The base metric to inherit from and modify"
    )
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

    # Variant's own settings (NOT inherited from source)
    version: int = Field(default=1, description="Version number for this variant")
    public: bool = Field(default=True, description="Whether this variant is publicly accessible")
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

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(pytz.UTC),
        description="When this variant was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(pytz.UTC),
        description="When this variant was last updated"
    )
