"""Admin response schemas"""
from cortex.core.types.telescope import TSModel


class CacheEvictionResponse(TSModel):
    """Response schema for cache eviction"""
    evicted_files: int
    status: str


class CacheStatusResponse(TSModel):
    """Response schema for cache status"""
    cache_size_gb: float
    max_size_gb: float
    entries_count: int
