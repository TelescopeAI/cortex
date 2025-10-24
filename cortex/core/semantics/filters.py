from typing import Optional, Any, Union, List
from pydantic import ConfigDict

from cortex.core.types.semantics.filter import FilterOperator, FilterType, FilterValueType
from cortex.core.types.semantics.column_source import ColumnSourceType, ColumnSourceMeta
from cortex.core.semantics.output_formats import OutputFormat
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.conditions import Condition


class SemanticFilter(TSModel):
    """
    Represents a filter condition used in semantic metrics for data filtering.
    
    A semantic filter defines how data should be filtered in WHERE or HAVING clauses.
    It serves as a building block for semantic metrics and is used in generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this filter
        description: A human-readable explanation of what this filter represents
        query: The column name or expression that defines this filter
        table: The source table or view where this filter's data resides
        operator: The comparison operator to use (equals, greater_than, etc.)
        value: The value to compare against
        value_type: The type of the value (string, number, boolean, etc.)
        filter_type: Whether this filter should be applied in WHERE or HAVING clause
        is_active: Whether this filter is currently active
        custom_expression: Optional custom SQL expression that overrides the standard filter logic
        conditional: Boolean flag to use conditional logic instead of query
        conditions: Condition object for CASE WHEN logic
    """
    name: str
    description: Optional[str] = None
    query: str  # Column name or expression
    table: Optional[str] = None  # Source table
    operator: Optional[FilterOperator] = None
    value: Optional[Any] = None  # The value to filter by
    value_type: FilterValueType = FilterValueType.STRING
    filter_type: FilterType = FilterType.WHERE  # Default to WHERE clause
    is_active: bool = True
    custom_expression: Optional[str] = None  # Custom SQL expression
    
    # For complex filters with multiple values (e.g., IN, BETWEEN)
    values: Optional[List[Any]] = None
    
    # For range filters (BETWEEN)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    
    # For dynamic filters that can be parameterized using $CORTEX_ prefix
    # Any field starting with $CORTEX_ will be treated as a parameter
    formatting: Optional[List[OutputFormat]] = None
    
    # Conditional logic support
    conditional: bool = False
    conditions: Optional[Condition] = None
    
    # Auto-inferred source column information
    source_type: Optional[ColumnSourceType] = None
    source_meta: Optional[ColumnSourceMeta] = None

    model_config = ConfigDict(use_enum_values=True) 