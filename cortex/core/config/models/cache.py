from typing import Optional

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.types.telescope import TSModel


class CacheConfig(TSModel):
    enabled: bool = False
    backend: str = "memory"  # "memory" | "redis"
    redis_url: Optional[str] = None
    ttl_seconds_default: int = 300

    @staticmethod
    def from_env() -> "CacheConfig":
        enabled = str(ExecutionEnv.get_key("CORTEX_CACHE_ENABLED", "false")).lower() == "true"
        backend_raw = ExecutionEnv.get_key("CORTEX_CACHE_BACKEND")
        # If backend is missing/blank and caching is enabled, default to memory
        backend = (backend_raw or "memory").strip().lower() if enabled else (backend_raw or "memory").strip().lower()
        print(f"[CORTEX CACHE] backend={backend} enabled={enabled}")
        print(f"[CORTEX CACHE] redis_url={ExecutionEnv.get_key('CORTEX_CACHE_REDIS_URL')}")
        print(f"[CORTEX CACHE] ttl_seconds_default={ExecutionEnv.get_key('CORTEX_CACHE_TTL_SECONDS_DEFAULT', '300')}")
        return CacheConfig(
            enabled=enabled,
            backend=backend or "memory",
            redis_url=ExecutionEnv.get_key("CORTEX_CACHE_REDIS_URL"),
            ttl_seconds_default=int(ExecutionEnv.get_key("CORTEX_CACHE_TTL_SECONDS_DEFAULT", "300")),
        )


