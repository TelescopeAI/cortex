from typing import Optional, Dict, Any
from enum import Enum
from cortex.core.types.telescope import TSModel


class TransformFunction(str, Enum):
    """SQL functions that can transform column values"""
    # String functions
    COALESCE = "COALESCE"
    LOWER = "LOWER"
    UPPER = "UPPER"
    CONCAT = "CONCAT"
    TRIM = "TRIM"
    SUBSTRING = "SUBSTRING"
    
    # Math functions
    ROUND = "ROUND"
    ABS = "ABS"
    CEIL = "CEIL"
    FLOOR = "FLOOR"
    
    # Date functions
    EXTRACT = "EXTRACT"
    DATE_TRUNC = "DATE_TRUNC"
    DATE_PART = "DATE_PART"
    
    # Type casting
    CAST = "CAST"


class Transform(TSModel):
    """
    A single transformation in a pipeline.
    Represents one SQL function applied to a column or previous transform result.
    
    Examples:
        Transform(function="COALESCE", params={"fallback": ""})
        Transform(function="LOWER")
        Transform(function="ROUND", params={"decimals": 2})
        Transform(function="EXTRACT", params={"part": "YEAR"})
    """
    function: TransformFunction
    params: Optional[Dict[str, Any]] = None
