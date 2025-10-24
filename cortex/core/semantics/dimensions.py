from typing import Optional, List

from cortex.core.types.semantics.column_source import ColumnSourceType, ColumnSourceMeta
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.conditions import Condition


class CombineColumnSpec(TSModel):
    """
    Specification for an additional column to combine with the dimension.
    Used to concatenate multiple columns into a single dimension value.
    
    Example: Combining first_name and last_name columns into a full_name dimension.
    
    Attributes:
        query: Column name or expression to combine
        table: Source table for the column (if different from dimension's table)
        delimiter: Separator to use before this column (default: space)
    """
    query: str
    table: Optional[str] = None
    delimiter: Optional[str] = " "


class SemanticDimension(TSModel):
    """
    Represents a categorical or descriptive attribute used in semantic metrics for analytics.
    
    A semantic dimension defines how data should be grouped, filtered, or categorized.
    It serves as a building block for semantic metrics and is used in generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this dimension
        description: A human-readable explanation of what this dimension represents
        query: The column name or expression that defines this dimension
        table: The source table or view where this dimension's data resides
        conditional: Boolean flag to use conditional logic instead of query
        conditions: Condition object for CASE WHEN logic
        source_type: Auto-inferred database column type for intelligent processing
        source_meta: Auto-inferred metadata about the source column
    """
    name: str
    description: Optional[str] = None
    query: str
    table: Optional[str] = None
    formatting: Optional[List[OutputFormat]] = None
    
    # Column combination
    combine: Optional[List[CombineColumnSpec]] = None
    
    # Conditional logic support
    conditional: bool = False
    conditions: Optional[Condition] = None
    
    # Auto-inferred source column information
    source_type: Optional[ColumnSourceType] = None
    source_meta: Optional[ColumnSourceMeta] = None
