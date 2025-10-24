from typing import Optional, List, Union, Any
from enum import Enum
from cortex.core.types.telescope import TSModel
from cortex.core.types.semantics.column_field import ColumnField


class ComparisonOperator(str, Enum):
    """Operators for comparing values in WHEN clauses"""
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class LogicalOperator(str, Enum):
    """Logical operators for combining multiple conditions"""
    AND = "AND"
    OR = "OR"


class WhenClause(TSModel):
    """
    A single WHEN condition in a CASE statement.
    Uses a linear pipeline approach for clarity.
    
    Example:
        WhenClause(
            field=ColumnField(column="status", table="orders"),
            operator=ComparisonOperator.IN,
            compare_values=["active", "pending"],
            then_return="Open"
        )
    """
    # What column to check (with optional transforms)
    field: ColumnField
    
    # How to compare
    operator: ComparisonOperator
    
    # What to compare against (primitives or another field)
    compare_values: Optional[Union[Any, List[Any], ColumnField]] = None
    
    # What to return when TRUE (primitive or field reference)
    then_return: Union[Any, ColumnField]
    
    # Optional: Combine multiple conditions with AND/OR
    combine_with: Optional[LogicalOperator] = None
    additional_conditions: Optional[List['WhenClause']] = None


class Condition(TSModel):
    """
    CASE WHEN statement with multiple conditions.
    Simple, flat structure - easy to build UI for.
    
    Example:
        Condition(
            when_clauses=[
                WhenClause(
                    field=ColumnField(column="amount"),
                    operator=ComparisonOperator.LESS_THAN,
                    compare_values=100,
                    then_return="Small"
                ),
                WhenClause(
                    field=ColumnField(column="amount"),
                    operator=ComparisonOperator.LESS_THAN,
                    compare_values=1000,
                    then_return="Medium"
                ),
            ],
            else_return="Large"
        )
    """
    when_clauses: List[WhenClause]
    else_return: Union[Any, ColumnField]
