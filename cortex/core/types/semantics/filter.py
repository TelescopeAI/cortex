from enum import Enum


class FilterOperator(str, Enum):
    """Supported filter operators for semantic filters"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_EQUALS = "greater_than_equals"
    LESS_THAN = "less_than"
    LESS_THAN_EQUALS = "less_than_equals"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    NOT_LIKE = "not_like"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"


class FilterType(str, Enum):
    """Types of filters - determines whether to use WHERE or HAVING clause"""
    WHERE = "where"  # Pre-aggregation filtering
    HAVING = "having"  # Post-aggregation filtering


class FilterValueType(str, Enum):
    """Types of values that can be used in filters"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    ARRAY = "array"
    NULL = "null" 