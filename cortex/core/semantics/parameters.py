from typing import Optional, Any, List
from enum import Enum

from cortex.core.types.telescope import TSModel


class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"


class ParameterDefinition(TSModel):
    """
    Defines parameters that can be injected into queries at runtime.
    """
    name: str
    type: ParameterType
    description: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = False
    allowed_values: Optional[List[Any]] = None  # For enum-like parameters
    validation_regex: Optional[str] = None  # For string validation
    min_value: Optional[float] = None  # For numeric parameters
    max_value: Optional[float] = None  # For numeric parameters 