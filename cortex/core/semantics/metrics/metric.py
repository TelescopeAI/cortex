from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

import pytz
from pydantic import Field, ConfigDict

from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.aggregations import SemanticAggregation
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.semantics.refresh_keys import RefreshKey
from cortex.core.semantics.parameters import ParameterDefinition
from cortex.core.types.telescope import TSModel


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
        output_formats: List of output format transformations
        parameters: Runtime parameters for dynamic query generation
    """
    model_config = ConfigDict(from_attributes=True)
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    data_model_id: UUID  # Foreign key to DataModel
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None  # Human-readable display name
    
    # Query definition
    query: Optional[str] = None  # Custom SQL query
    table_name: Optional[str] = None  # Source table
    data_source: Optional[str] = "default"  # Data source name for multi-database support
    
    # Metric components
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    aggregations: Optional[List[SemanticAggregation]] = None
    output_formats: Optional[List[OutputFormat]] = None
    
    # Parameters for dynamic query generation
    parameters: Optional[Dict[str, ParameterDefinition]] = None
    
    # Version tracking
    model_version: int = 1  # Version of the model this metric belongs to
    
    # Visibility control
    public: bool = True  # Whether this metric can be queried via API
    
    # Caching and refresh
    refresh_key: Optional[RefreshKey] = None
    
    # Custom metadata
    meta: Optional[Dict[str, Any]] = None
    
    # Validation and compilation
    is_valid: bool = False
    validation_errors: Optional[List[str]] = None
    compiled_query: Optional[str] = None  # Generated SQL
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


