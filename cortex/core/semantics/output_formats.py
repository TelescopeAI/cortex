from typing import List, Optional
from enum import Enum

from cortex.core.types.telescope import TSModel


class OutputFormatType(str, Enum):
    RAW = "raw"                    # No transformation
    COMBINE = "combine"            # Combine multiple columns
    CALCULATE = "calculate"        # Mathematical operations
    FORMAT = "format"              # String formatting
    CAST = "cast"                  # Type casting
    AGGREGATE = "aggregate"        # Apply aggregations


class OutputFormat(TSModel):
    """
    Defines how metric results should be transformed before returning to users.
    """
    name: str
    type: OutputFormatType
    description: Optional[str] = None
    
    # For COMBINE type
    source_columns: Optional[List[str]] = None
    delimiter: Optional[str] = None
    
    # For CALCULATE type
    operation: Optional[str] = None  # e.g., "add", "subtract", "multiply", "divide"
    operands: Optional[List[str]] = None
    
    # For CAST type
    target_type: Optional[str] = None  # e.g., "string", "integer", "float", "date"
    
    # For FORMAT type
    format_string: Optional[str] = None  # e.g., "%.2f", "YYYY-MM-DD"
    
    # For AGGREGATE type - reference to an aggregation (avoid circular import)
    aggregation_name: Optional[str] = None 