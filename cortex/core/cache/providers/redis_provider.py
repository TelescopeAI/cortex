from typing import Optional

try:
    import redis  # type: ignore
except Exception as e:  # pragma: no cover - optional dependency
    print(f"Redis exception {str(e)}")
    redis = None

from cortex.core.cache.storage import CacheStorage


class RedisCache(CacheStorage):
    """Redis/Valkey/KeyDB compatible provider using redis-py when available.

    Renamed to avoid module name shadowing issues with the third-party 'redis' package.
    """

    def __init__(self, url: str):
        if redis is None:
            raise RuntimeError("redis package is not installed")
        self._client = redis.from_url(url)  # type: ignore
        # Validate connectivity early to surface configuration/network issues
        try:
            self._client.ping()
            print(f"[CORTEX CACHE] Redis connected: {url}")
        except Exception as e:  # pragma: no cover - runtime connectivity
            raise RuntimeError(f"Redis connection failed: {e}")

    def get(self, key: str) -> Optional[bytes]:
        value = self._client.get(key)
        return value

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        if ttl_seconds and ttl_seconds > 0:
            self._client.set(name=key, value=value, ex=ttl_seconds)
        else:
            self._client.set(name=key, value=value)

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def clear(self) -> None:
        # No safe global clear; noop by default.
        pass
