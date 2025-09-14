from enum import Enum


class SemanticOrderType(str, Enum):
    """
    Enum defining the order type for semantic order sequences.
    """
    ASC = "asc"
    DESC = "desc"


class SemanticNullsPosition(str, Enum):
    """
    Enum defining where null values should be positioned in the sort order.
    """
    FIRST = "first"
    LAST = "last"
