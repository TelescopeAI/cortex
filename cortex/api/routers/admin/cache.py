"""Admin cache management router"""
from fastapi import APIRouter, Depends, HTTPException
from cortex.api.schemas.responses.admin.cache import CacheEvictionResponse, CacheStatusResponse
from cortex.api.dependencies.admin_auth import verify_admin_api_key
from cortex.core.config.execution_env import ExecutionEnv
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexSDKError

# Get include_in_schema from env (defaults to False)
SHOW_ADMIN_IN_DOCS = ExecutionEnv.get_key("CORTEX_SHOW_ADMIN_API_IN_DOCS", "false").lower() == "true"

AdminCacheRouter = APIRouter(
    prefix="/admin/cache",
    tags=["Admin"],
    dependencies=[Depends(verify_admin_api_key)],
    include_in_schema=SHOW_ADMIN_IN_DOCS
)

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@AdminCacheRouter.post("/evict", response_model=CacheEvictionResponse)
async def evict_cache() -> CacheEvictionResponse:
    """Evict LRU cache entries to free space

    This endpoint should be called by the jobs server in distributed deployments
    to trigger cache eviction on the API server's local SSD.

    Requires: X-Admin-API-Key header with valid CORTEX_ADMIN_API_KEY

    Returns:
        CacheEvictionResponse with number of evicted files and status
    """
    try:
        return _client.admin.evict_cache()
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@AdminCacheRouter.get("/status", response_model=CacheStatusResponse)
async def get_cache_status() -> CacheStatusResponse:
    """Get current cache statistics

    This endpoint provides information about the current state of the local SSD cache,
    useful for monitoring and debugging.

    Requires: X-Admin-API-Key header with valid CORTEX_ADMIN_API_KEY

    Returns:
        CacheStatusResponse with cache size, max size, and entry count
    """
    try:
        return _client.admin.get_cache_status()
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))
