"""Central registry for all Plombery background jobs"""
from cortex.jobs.tasks.cache_eviction import register_cache_eviction_pipeline
from plombery import get_app


def register_all_pipelines():
    """Register all background job pipelines"""
    # Register cache eviction pipeline
    register_cache_eviction_pipeline()
    
    return get_app()
