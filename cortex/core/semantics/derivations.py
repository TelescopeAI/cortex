"""
Derivation models for composable metrics system.

This module defines derived entities (currently measures, future: dimensions) that are computed
from other entities using window functions or arithmetic operations.
"""

from typing import Any, List, Optional
from enum import Enum

from pydantic import Field

from cortex.core.types.telescope import TSModel
from cortex.core.semantics.output_formats import OutputFormat


class DerivedEntityType(str, Enum):
    """Types of derived entities supporting window functions and arithmetic operations."""

    # Aggregate-as-window (custom Cortex derivations)
    PERCENT_OF_TOTAL = "percent_of_total"
    RUNNING_TOTAL = "running_total"
    CUMULATIVE_COUNT = "cumulative_count"
    SHARE = "share"

    # Arithmetic (two-input operations)
    DIVIDE = "divide"
    MULTIPLY = "multiply"
    SUBTRACT = "subtract"
    ADD = "add"

    # PostgreSQL general-purpose window functions
    ROW_NUMBER = "row_number"
    RANK = "rank"
    DENSE_RANK = "dense_rank"
    PERCENT_RANK = "percent_rank"
    CUME_DIST = "cume_dist"
    NTILE = "ntile"
    LAG = "lag"
    LEAD = "lead"
    FIRST_VALUE = "first_value"
    LAST_VALUE = "last_value"
    NTH_VALUE = "nth_value"


class SourceRef(TSModel):
    """
    Reference to source measure(s) for a derivation.

    For single-input derivations (e.g., percent_of_total), only `measure` is needed.
    For two-input derivations (e.g., divide), both `measure` and `by` are required.

    Cross-CTE references use dot notation: "alias.measure"
    """
    measure: str = Field(
        ...,
        description="Primary measure name (or alias.measure for cross-CTE references)"
    )
    by: Optional[str] = Field(
        default=None,
        description="Second operand for two-input ops (divide, multiply, subtract, add)"
    )


class DerivedEntity(TSModel):
    """
    An entity (currently measure, future: dimension) computed from other entities
    via window functions or arithmetic operations.

    This model is future-proofed to support derived dimensions in addition to derived measures.
    """
    name: str = Field(..., description="Name of the derived entity")
    type: DerivedEntityType = Field(..., description="Type of derivation to apply")
    source: SourceRef = Field(..., description="Source entity reference(s)")

    # Window function parameters
    order_dimension: Optional[str] = Field(
        default=None,
        description="Dimension to order by (for running_total, cumulative_count, and ORDER BY-dependent window funcs)"
    )
    partition_by: Optional[str] = Field(
        default=None,
        description="Dimension to partition by (for share and PARTITION BY in window funcs)"
    )

    # Offset window function parameters
    offset: Optional[int] = Field(
        default=None,
        description="Offset value for lag/lead (default 1)"
    )
    default_value: Optional[Any] = Field(
        default=None,
        description="Default value for lag/lead when offset goes out of bounds (default NULL)"
    )

    # Special window function parameters
    n: Optional[int] = Field(
        default=None,
        description="For ntile (bucket count) and nth_value (row position)"
    )

    # Output formatting
    formatting: Optional[List[OutputFormat]] = Field(
        default=None,
        description="Optional output formatting rules for the derived entity"
    )
