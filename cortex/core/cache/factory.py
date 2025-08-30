from typing import Optional

from cortex.core.cache.providers.inmemory import InMemoryCache
from cortex.core.cache.providers.redis_provider import RedisCache
from cortex.core.cache.storage import CacheStorage
from cortex.core.config.models.cache import CacheConfig


def create_cache_storage(config: CacheConfig) -> CacheStorage:
    backend = (config.backend or "memory").lower()
    print(f"[CORTEX CACHE] create storage backend={backend}")
    if backend == "redis":
        if not config.redis_url:
            raise ValueError("CORTEX_CACHE_REDIS_URL must be set when using redis backend")
        try:
            return RedisCache(url=config.redis_url)
        except Exception as e:
            print(f"[CORTEX CACHE] Redis backend init failed: {e}")
            raise RuntimeError("Failed to initialize Redis cache backend") from e
    return InMemoryCache()


_GLOBAL_STORAGE: Optional[CacheStorage] = None
_GLOBAL_BACKEND_KEY: Optional[str] = None


def get_cache_storage(config: Optional[CacheConfig] = None) -> CacheStorage:
    """Return a singleton cache storage for the process.

    Ensures InMemory provider yields cache hits across requests in the same worker.
    If backend config changes, a new storage is created.
    """
    global _GLOBAL_STORAGE, _GLOBAL_BACKEND_KEY
    cfg = config or CacheConfig.from_env()
    backend_key = f"{cfg.backend}:{cfg.redis_url or ''}"
    if _GLOBAL_STORAGE is None or _GLOBAL_BACKEND_KEY != backend_key:
        _GLOBAL_STORAGE = create_cache_storage(cfg)
        _GLOBAL_BACKEND_KEY = backend_key
    return _GLOBAL_STORAGE

