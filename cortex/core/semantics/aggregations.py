from typing import Optional, List, Dict, Any
from enum import Enum

from cortex.core.types.telescope import TSModel


class AggregationType(str, Enum):
    # Basic aggregations
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    
    # Statistical aggregations
    STDDEV = "stddev"
    VARIANCE = "variance"
    PERCENTILE = "percentile"
    MEDIAN = "median"
    
    # Window functions
    ROW_NUMBER = "row_number"
    RANK = "rank"
    DENSE_RANK = "dense_rank"
    LAG = "lag"
    LEAD = "lead"
    
    # Custom aggregations
    CUSTOM = "custom"


class AggregationWindow(TSModel):
    """
    Defines window function parameters for aggregations.
    """
    partition_by: Optional[List[str]] = None
    order_by: Optional[List[str]] = None
    frame_start: Optional[str] = None  # e.g., "UNBOUNDED PRECEDING", "CURRENT ROW"
    frame_end: Optional[str] = None    # e.g., "UNBOUNDED FOLLOWING", "CURRENT ROW"


class SemanticAggregation(TSModel):
    """
    Defines aggregations that can be applied to metrics.
    """
    name: str
    description: Optional[str] = None
    type: AggregationType
    source_columns: List[str]  # Columns to aggregate
    target_column: str         # Result column name
    
    # For custom aggregations
    custom_expression: Optional[str] = None
    
    # For window functions
    window: Optional[AggregationWindow] = None
    
    # For percentile aggregations
    percentile_value: Optional[float] = None  # e.g., 0.95 for 95th percentile
    
    # For conditional aggregations
    where_condition: Optional[str] = None
    
    # For grouped aggregations
    group_by_columns: Optional[List[str]] = None 