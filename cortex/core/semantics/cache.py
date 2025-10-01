from typing import Optional

from pydantic import Field

from cortex.core.types.telescope import TSModel


class CachePreference(TSModel):
    """Result cache configuration for metrics and requests.

    - enabled: whether caching is on
    - ttl: time-to-live in seconds (if omitted, fallback to backend default)
    """

    enabled: bool = Field(default=True, description="Enable result caching")
    ttl: Optional[int] = Field(default=None, description="Cache TTL in seconds")


