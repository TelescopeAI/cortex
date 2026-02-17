"""
Override models for composable metrics system.

This module defines how metric variants can override components from their source metrics
using structured add/replace/exclude/include operations.
"""

from typing import Optional, List

from pydantic import Field

from cortex.core.types.telescope import TSModel
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.order_sequences import SemanticOrderSequence


class OverrideComponents(TSModel):
    """
    Strictly typed bundle of components for add/replace operations.

    Contains full component definitions that will be added to or replace
    existing components in the resolved metric.
    """
    measures: Optional[List[SemanticMeasure]] = Field(
        default=None,
        description="Measures to add or replace"
    )
    dimensions: Optional[List[SemanticDimension]] = Field(
        default=None,
        description="Dimensions to add or replace"
    )
    filters: Optional[List[SemanticFilter]] = Field(
        default=None,
        description="Filters to add or replace"
    )
    joins: Optional[List[SemanticJoin]] = Field(
        default=None,
        description="Joins to add or replace"
    )
    order: Optional[List[SemanticOrderSequence]] = Field(
        default=None,
        description="Order sequences to add or replace"
    )


class ExcludeComponents(TSModel):
    """
    Names of components to remove from the source metric.

    Only component names are needed for exclusion (not full objects),
    as we're just filtering out by name.
    """
    measures: Optional[List[str]] = Field(
        default=None,
        description="Names of measures to exclude"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Names of dimensions to exclude"
    )
    filters: Optional[List[str]] = Field(
        default=None,
        description="Names of filters to exclude"
    )
    joins: Optional[List[str]] = Field(
        default=None,
        description="Names of joins to exclude"
    )


class MetricOverrides(TSModel):
    """
    Operation-first override structure for modifying source metrics.

    Resolution order: inherit → include → exclude → replace → add

    Scalar overrides (table_name, limit, etc.) are applied directly without
    going through add/replace/exclude operations.
    """
    # Component operations
    add: Optional[OverrideComponents] = Field(
        default=None,
        description="Components to add to the resolved metric"
    )
    replace: Optional[OverrideComponents] = Field(
        default=None,
        description="Components to replace (matched by name)"
    )
    exclude: Optional[ExcludeComponents] = Field(
        default=None,
        description="Component names to exclude from source"
    )

    # Scalar field overrides
    table_name: Optional[str] = Field(
        default=None,
        description="Override the source table name"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Override the query limit"
    )
    grouped: Optional[bool] = Field(
        default=None,
        description="Override the grouped flag"
    )
    ordered: Optional[bool] = Field(
        default=None,
        description="Override the ordered flag"
    )


class IncludedComponents(TSModel):
    """
    Whitelist for inheriting only specific components from source (by name).

    When include is specified, only components whose names are in these lists
    will be inherited from the source metric. All others are excluded.

    If include is not specified, all source components are inherited by default
    (unless explicitly excluded).
    """
    measures: Optional[List[str]] = Field(
        default=None,
        description="Names of measures to include from source"
    )
    dimensions: Optional[List[str]] = Field(
        default=None,
        description="Names of dimensions to include from source"
    )
    filters: Optional[List[str]] = Field(
        default=None,
        description="Names of filters to include from source"
    )
    joins: Optional[List[str]] = Field(
        default=None,
        description="Names of joins to include from source"
    )
