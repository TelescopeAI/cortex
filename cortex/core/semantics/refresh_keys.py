from typing import Optional
from enum import Enum

from cortex.core.types.telescope import TSModel
from pydantic import Field


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
    sql: Optional[str] = None    # Custom SQL refresh condition
    max: Optional[str] = None    # Column name to check max value
    cache: Optional["CachePreference"] = None


class CachePreference(TSModel):
    """Execution-time caching preference. Overrides metric-level enablement.
    """
    enabled: bool = Field(default=True)


# Resolve forward reference
RefreshKey.model_rebuild() 