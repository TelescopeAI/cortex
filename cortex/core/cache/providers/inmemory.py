import time
from collections import OrderedDict
from typing import Optional

from cortex.core.cache.storage import CacheStorage


class InMemoryCache(CacheStorage):
    """A simple in-memory cache with TTL and LRU-like behavior.

    This is intentionally minimal and dependency-free.
    """

    def __init__(self, max_items: int = 1024):
        self._store: OrderedDict[str, tuple[bytes, Optional[float]]] = OrderedDict()
        self._max_items = max_items

    def get(self, key: str) -> Optional[bytes]:
        entry = self._store.get(key)
        if not entry:
            return None
        value, expires_at = entry
        if expires_at is not None and time.time() >= expires_at:
            # expired; remove
            try:
                del self._store[key]
            except KeyError:
                pass
            return None
        # move to end to indicate recent use
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds and ttl_seconds > 0 else None
        self._store[key] = (value, expires_at)
        self._store.move_to_end(key)
        # enforce max size
        if len(self._store) > self._max_items:
            self._store.popitem(last=False)

    def delete(self, key: str) -> None:
        try:
            del self._store[key]
        except KeyError:
            return

    def clear(self) -> None:
        self._store.clear()
