"""Admin cache management router"""
from fastapi import APIRouter, Depends
from cortex.api.schemas.responses.admin.cache import CacheEvictionResponse, CacheStatusResponse
from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.api.dependencies.admin_auth import verify_admin_api_key
from cortex.core.config.execution_env import ExecutionEnv

# Get include_in_schema from env (defaults to False)
SHOW_ADMIN_IN_DOCS = ExecutionEnv.get_key("CORTEX_SHOW_ADMIN_API_IN_DOCS", "false").lower() == "true"

AdminCacheRouter = APIRouter(
    prefix="/admin/cache",
    tags=["Admin"],
    dependencies=[Depends(verify_admin_api_key)],
    include_in_schema=SHOW_ADMIN_IN_DOCS
)


@AdminCacheRouter.post("/evict", response_model=CacheEvictionResponse)
async def evict_cache() -> CacheEvictionResponse:
    """Evict LRU cache entries to free space
    
    This endpoint should be called by the jobs server in distributed deployments
    to trigger cache eviction on the API server's local SSD.
    
    Requires: X-Admin-API-Key header with valid CORTEX_ADMIN_API_KEY
    
    Returns:
        CacheEvictionResponse with number of evicted files and status
    """
    config = get_sheets_config()
    cache_manager = CortexFileStorageCacheManager(
        cache_dir=config.cache_dir,
        sqlite_dir=config.sqlite_storage_path,
        max_size_gb=config.cache_max_size_gb
    )
    evicted_count = cache_manager.evict_lru()
    return CacheEvictionResponse(evicted_files=evicted_count, status="success")


@AdminCacheRouter.get("/status", response_model=CacheStatusResponse)
async def get_cache_status() -> CacheStatusResponse:
    """Get current cache statistics
    
    This endpoint provides information about the current state of the local SSD cache,
    useful for monitoring and debugging.
    
    Requires: X-Admin-API-Key header with valid CORTEX_ADMIN_API_KEY
    
    Returns:
        CacheStatusResponse with cache size, max size, and entry count
    """
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
