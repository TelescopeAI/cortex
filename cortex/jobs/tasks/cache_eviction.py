"""Cache eviction task - runs every 2 hours"""
import logging
from apscheduler.triggers.interval import IntervalTrigger

from plombery import task, register_pipeline, Trigger
from cortex.core.config.execution_env import ExecutionEnv

logger = logging.getLogger(__name__)


@task
async def evict_file_storage_cache():
    """Evict least recently used SQLite databases from cache
    
    In distributed deployments, calls the admin API on the API server.
    In local deployments, directly accesses the cache manager.
    """
    # Check if we should use remote API or local cache manager
    api_base_url = ExecutionEnv.get_key("CORTEX_API_BASE_URL", "")
    
    if api_base_url:
        # Distributed deployment - use admin API
        logger.info("Using remote admin API for cache eviction")
        from cortex.jobs.clients.api_client import CortexAdminAPIClient
        
        client = CortexAdminAPIClient()
        result = await client.evict_cache()
        return result
    else:
        # Local deployment - direct cache access
        logger.info("Using local cache manager for cache eviction")
        from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
        from cortex.core.connectors.api.sheets.config import get_sheets_config
        
        config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=config.cache_dir,
            max_size_gb=config.cache_max_size_gb
        )
        evicted_count = cache_manager.evict_lru()
        return {"evicted_files": evicted_count, "status": "success"}


def register_cache_eviction_pipeline():
    """Register cache eviction pipeline with 2-hour interval"""
    register_pipeline(
        id="file_storage_cache_eviction",
        name="File Storage Cache Eviction",
        description="Evict least recently used SQLite databases from cache",
        tasks=[evict_file_storage_cache],
        triggers=[
            Trigger(
                id="file_storage_cache_eviction",
                name="File Storage Cache Eviction",
                description="Evict least recently used SQLite databases from cache every 2 hours",
                schedule=IntervalTrigger(hours=1),
            )
        ],
    )
