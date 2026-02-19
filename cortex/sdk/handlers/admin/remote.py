"""
Admin remote handler - HTTP API calls.

Handles admin operations in API mode.
"""
from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.responses.admin.cache import (
    CacheEvictionResponse,
    CacheStatusResponse
)


def evict_cache(client: CortexHTTPClient) -> CacheEvictionResponse:
    """
    Evict LRU cache entries to free space - HTTP API call.

    Args:
        client: HTTP client

    Returns:
        Cache eviction response with number of evicted files
    """
    response = client.post("/admin/cache/evict")
    return CacheEvictionResponse(**response)


def get_cache_status(client: CortexHTTPClient) -> CacheStatusResponse:
    """
    Get current cache statistics - HTTP API call.

    Args:
        client: HTTP client

    Returns:
        Cache status response with size and entry count
    """
    response = client.get("/admin/cache/status")
    return CacheStatusResponse(**response)
