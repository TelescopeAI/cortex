"""
Admin direct handler - Core service calls.

Handles admin operations in Direct mode.
"""
from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.sdk.schemas.responses.admin.cache import (
    CacheEvictionResponse,
    CacheStatusResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper


def evict_cache() -> CacheEvictionResponse:
    """
    Evict LRU cache entries to free space - direct Core service call.

    This operation should be called by the jobs server in distributed deployments
    to trigger cache eviction on the API server's local SSD.

    Returns:
        Cache eviction response with number of evicted files
    """
    try:
        config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=config.cache_dir,
            sqlite_dir=config.sqlite_storage_path,
            max_size_gb=config.cache_max_size_gb
        )
        evicted_count = cache_manager.evict_lru()
        return CacheEvictionResponse(evicted_files=evicted_count, status="success")
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_cache_status() -> CacheStatusResponse:
    """
    Get current cache statistics - direct Core service call.

    This operation provides information about the current state of the local SSD cache,
    useful for monitoring and debugging.

    Returns:
        Cache status response with size and entry count
    """
    try:
        config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=config.cache_dir,
            sqlite_dir=config.sqlite_storage_path,
            max_size_gb=config.cache_max_size_gb
        )
        return CacheStatusResponse(
            cache_size_gb=cache_manager._get_cache_size_gb(),
            max_size_gb=config.cache_max_size_gb,
            entries_count=cache_manager.get_entries_count()
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)
