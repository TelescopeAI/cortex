from typing import List, Optional, Dict
from enum import Enum

from pydantic import Field

from cortex.core.types.telescope import TSModel


class OutputFormatType(str, Enum):
    RAW = "raw"                    # No transformation
    COMBINE = "combine"            # Combine multiple columns (DEPRECATED: Use SemanticDimension.combine instead)
    CALCULATE = "calculate"        # Mathematical operations
    FORMAT = "format"              # String formatting
    CAST = "cast"                  # Type casting


class OutputFormatMode(str, Enum):
    IN_QUERY = "in_query"          # Processing done directly in SQL query
    POST_QUERY = "post_query"      # Processing done after query results received


class FormatType(str, Enum):
    DATETIME = "datetime"          # Date/time formatting
    NUMBER = "number"              # Number formatting
    CURRENCY = "currency"          # Currency formatting
    PERCENTAGE = "percentage"      # Percentage formatting
    CUSTOM = "custom"              # Custom format string


# Type alias for the formatting map
FormattingMap = Dict[str, List['OutputFormat']]


class OutputFormat(TSModel):
    """
    Defines how metric results should be transformed before returning to users.
    """
    name: str
    type: OutputFormatType
    description: Optional[str] = None
    mode: Optional[OutputFormatMode] = Field(default=OutputFormatMode.IN_QUERY)  # Default to in-query processing

    # For COMBINE type
    source_columns: Optional[List[str]] = None
    delimiter: Optional[str] = None
    
    # For CALCULATE type
    operation: Optional[str] = None  # e.g., "add", "subtract", "multiply", "divide"
    operands: Optional[List[str]] = None
    
    # For CAST type
    target_type: Optional[str] = None  # e.g., "string", "integer", "float", "date"
    
    # For FORMAT type
    format_type: Optional[FormatType] = Field(default=FormatType.DATETIME, description="Type of formatting to apply")
    format_string: Optional[str] = None  # e.g., "%.2f", "YYYY-MM-DD", "DD-MM-YYYY" 