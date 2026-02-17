from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

import pytz
from pydantic import Field, ConfigDict, model_validator

from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.order_sequences import SemanticOrderSequence
from cortex.core.semantics.refresh_keys import RefreshPolicy
from cortex.core.semantics.cache import CachePreference
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.derivations import DerivedEntity


class MetricRef(TSModel):
    """
    Reference to a saved or inline metric.

    Supports two modes:
    - ID reference: metric_id points to a saved metric
    - Inline reference: metric contains a full SemanticMetric definition

    Used in variant source definitions and multi-source composition (combine).
    """
    metric_id: Optional[UUID] = Field(
        default=None,
        description="ID of a saved metric (mutually exclusive with metric)"
    )
    metric: Optional['SemanticMetric'] = Field(
        default=None,
        description="Inline metric definition (mutually exclusive with metric_id)"
    )
    alias: Optional[str] = Field(
        default=None,
        description="Alias for this metric in CTE context"
    )
    join_on: Optional[List[str]] = Field(
        default=None,
        description="List of dimension names to join on (for combine scenarios)"
    )

    @model_validator(mode='after')
    def validate_exactly_one(self):
        """Ensure exactly one of metric_id or metric is provided."""
        if self.metric_id is None and self.metric is None:
            raise ValueError("MetricRef requires either metric_id or metric")
        if self.metric_id is not None and self.metric is not None:
            raise ValueError("MetricRef cannot have both metric_id and metric")
        return self


class CompositionSource(TSModel):
    """
    A fully-resolved sub-metric that becomes a CTE in the generated query.

    This is populated by the compiler during variant resolution (not by users directly).
    When a metric has composition populated, the query engine generates a CTE query
    instead of a simple SELECT.

    The composition is stored in the database to avoid recompiling on every execution.
    """
    alias: str = Field(
        ...,
        description="Alias for this sub-metric's CTE in the generated SQL"
    )
    metric: 'SemanticMetric' = Field(
        ...,
        description="Resolved sub-metric with its own table, measures, and dimensions"
    )
    join_on: List[str] = Field(
        ...,
        description="Shared dimension names for JOIN clause in outer query"
    )


class SemanticMetric(TSModel):
    """
    Semantic metric that defines what data should be measured and how it can be sliced for analysis.
    
    Each metric belongs to a data model and contains its own measures, dimensions, joins, and aggregations.
    Metrics can be executed independently and support custom SQL queries.
    
    Attributes:
        data_model_id: The ID of the data model this metric belongs to
        name: The unique identifier name for this metric
        description: A human-readable explanation of what this metric represents
        query: Optional custom query string that can override the auto-generated query
        table_name: The source table or view where this metric's data resides
        measures: List of quantitative measurements included in this metric
        dimensions: List of categorical attributes by which the measures can be grouped
        joins: List of joins to be applied in the query
        aggregations: List of aggregations to be applied to the data
        order: List of order sequences defining how results should be sorted
        parameters: Runtime parameters for dynamic query generation
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    environment_id: UUID  # Foreign key to Environment
    data_model_id: UUID  # Foreign key to DataModel
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None  # Human-readable display name
    
    # Query definition
    query: Optional[str] = None  # Custom SQL query
    table_name: Optional[str] = None  # Source table
    data_source_id: Optional[UUID] = None  # Foreign key to the data source
    limit: Optional[int] = None  # Default limit for query results
    grouped: Optional[bool] = Field(default=True, description="Whether to apply GROUP BY when dimensions are present")
    ordered: Optional[bool] = Field(default=True, description="Whether to apply ORDER BY for sorting results")
    
    # Metric components
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    filters: Optional[List[SemanticFilter]] = None
    order: Optional[List[SemanticOrderSequence]] = None
    
    # Parameters for dynamic query generation
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    
    # Version tracking
    version: int = 1  # Metric version for caching invalidation and change tracking

    # Composable metrics (new fields for compiler system)
    derivations: Optional[List[DerivedEntity]] = Field(
        default=None,
        description="Derived entities (currently measures, future: dimensions) computed via window functions or arithmetic"
    )
    composition: Optional[List[CompositionSource]] = Field(
        default=None,
        description="Resolved CTE sub-metrics (populated by compiler, stored in DB to avoid recompilation)"
    )

    # Visibility control
    public: bool = True  # Whether this metric can be queried via API
    
    # Caching and refresh
    refresh: Optional[RefreshPolicy] = Field(default=None, description="Pre-aggregation refresh policy")
    cache: Optional[CachePreference] = Field(default=None, description="Result cache preference")
    
    # Custom metadata
    meta: Optional[Dict[str, Any]] = None
    
    # Validation and compilation
    is_valid: bool = False
    validation_errors: Optional[List[str]] = None
    compiled_query: Optional[str] = None  # Generated SQL
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
