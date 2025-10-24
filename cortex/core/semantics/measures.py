from typing import Optional, List

from pydantic import ConfigDict

from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.types.semantics.column_source import ColumnSourceType, ColumnSourceMeta
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.conditions import Condition


class SemanticMeasure(TSModel):
    """
    Represents a quantitative measurement used in semantic metrics for analytics.
    
    A semantic measure defines what data should be quantified and how it should be
    calculated and formatted. It serves as a building block for semantic metrics
    and is used in generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this measure
        description: A human-readable explanation of what this measure represents
        type: The calculation type (e.g., count, sum, average) to be applied
        format: Optional formatting instructions for the measure's output values
        alias: Optional alternative name to use in queries and results
        query: Optional custom query expression that defines this measure
        conditional: Boolean flag to use conditional logic instead of query
        conditions: Condition object for CASE WHEN logic
        table: The source table or view where this measure's data resides
        primary_key: Optional identifier for the primary key column of the table
        source_type: Auto-inferred database column type for intelligent processing
        source_meta: Auto-inferred metadata about the source column
    """
    name: str
    description: Optional[str]
    type: SemanticMeasureType
    formatting: Optional[List[OutputFormat]] = None
    alias: Optional[str] = None
    query: Optional[str] = None
    table: Optional[str] = None
    primary_key: Optional[str] = None
    
    # Conditional logic support
    conditional: bool = False
    conditions: Optional[Condition] = None
    
    # Auto-inferred source column information
    source_type: Optional[ColumnSourceType] = None
    source_meta: Optional[ColumnSourceMeta] = None

    model_config = ConfigDict(use_enum_values=True)
