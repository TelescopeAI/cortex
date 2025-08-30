import json
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from cortex.core.cache.storage import CacheStorage


class QueryCacheManager:
    """High-level cache manager for query results.

    Encodes/decodes payloads and enforces TTL decisions passed by the caller.
    """

    def __init__(self, storage: CacheStorage):
        self.storage = storage

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self.storage.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int]) -> None:
        raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.storage.set(key, raw, ttl_seconds)

    def delete(self, key: str) -> None:
        self.storage.delete(key)
