from typing import Optional
from enum import Enum

from cortex.core.types.telescope import TSModel


class RefreshKeyType(str, Enum):
    EVERY = "every"           # Refresh every X time units
    SQL = "sql"              # Custom SQL refresh condition
    MAX = "max"              # Refresh based on max value


class RefreshKey(TSModel):
    """
    Defines when metric data should be refreshed/cached.
    """
    type: RefreshKeyType
    every: Optional[str] = None  # e.g., "1 hour", "30 minutes", "1 day"
    sql: Optional[str] = None    # Custom SQL to check if refresh is needed
    max: Optional[str] = None    # Column name to check max value 