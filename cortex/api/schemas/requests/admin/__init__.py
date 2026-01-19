"""Admin request schemas"""
from cortex.core.types.telescope import TSModel


class CacheEvictionRequest(TSModel):
    """Request schema for cache eviction (currently no parameters)"""
    pass
