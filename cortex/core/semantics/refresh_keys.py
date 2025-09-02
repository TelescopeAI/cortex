from typing import Optional
from enum import Enum

from cortex.core.types.telescope import TSModel
from pydantic import Field


class RefreshType(str, Enum):
    EVERY = "every"           # Refresh every X time units
    SQL = "sql"              # Custom SQL refresh condition
    MAX = "max"              # Refresh based on max value


class RefreshPolicy(TSModel):
    """
    Pre-aggregation (rollup/materialized view) refresh policy.
    """
    type: RefreshType = Field(description="Refresh strategy")
    every: Optional[str] = Field(default=None, description="e.g., '1 hour', '30 minutes', '1 day'")
    sql: Optional[str] = Field(default=None, description="Custom SQL to check if refresh is needed")
    max: Optional[str] = Field(default=None, description="Column name to check max value") 