from typing import Optional, List
from enum import Enum

from cortex.core.types.telescope import TSModel


class JoinType(str, Enum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    FULL = "full"
    CROSS = "cross"


class JoinCondition(TSModel):
    """
    Defines a join condition between tables.
    """
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    operator: str = "="  # e.g., "=", ">", "<", ">=", "<=", "!="


class SemanticJoin(TSModel):
    """
    Enhanced join definition for semantic models.
    """
    name: str
    description: Optional[str] = None
    join_type: JoinType
    left_table: str
    right_table: str
    conditions: List[JoinCondition]
    alias: Optional[str] = None  # Optional alias for the joined table

