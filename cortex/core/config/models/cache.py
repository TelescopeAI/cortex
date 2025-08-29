import os
from typing import Optional

from cortex.core.types.telescope import TSModel


class CacheConfig(TSModel):
    enabled: bool = False
    backend: str = "memory"  # "memory" | "redis"
    redis_url: Optional[str] = None
    ttl_seconds_default: int = 300

    @staticmethod
    def from_env() -> "CacheConfig":
        enabled = os.getenv("CORTEX_CACHE_ENABLED", "false").lower() == "true"
        backend_raw = os.getenv("CORTEX_CACHE_BACKEND")
        # If backend is missing/blank and cache is enabled, default to memory
        backend = (backend_raw or "memory").strip().lower() if enabled else (backend_raw or "memory").strip().lower()
        print(f"[CORTEX CACHE] backend={backend} enabled={enabled}")
        print(f"[CORTEX CACHE] redis_url={os.getenv('CORTEX_CACHE_REDIS_URL')}")
        print(f"[CORTEX CACHE] ttl_seconds_default={os.getenv('CORTEX_CACHE_TTL_SECONDS_DEFAULT', '300')}")
        return CacheConfig(
            enabled=enabled,
            backend=backend or "memory",
            redis_url=os.getenv("CORTEX_CACHE_REDIS_URL"),
            ttl_seconds_default=int(os.getenv("CORTEX_CACHE_TTL_SECONDS_DEFAULT", "300")),
        )


