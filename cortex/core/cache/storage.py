from typing import Optional, Protocol, List


class CacheStorage(Protocol):
    """Minimal cache storage interface for portability across providers.

    Providers may ignore TTL if unsupported. Advanced features (locking, scans)
    can be implemented via optional mixin protocols.
    """

    def get(self, key: str) -> Optional[bytes]:
        ...

    def set(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...

    def clear(self) -> None:
        """Optional convenience for in-memory/testing providers."""
        ...


class LockingCacheStorage(Protocol):
    """Optional locking interface for providers that support it."""

    def acquire_lock(self, name: str, ttl_seconds: int) -> Optional[str]:
        ...

    def release_lock(self, name: str, token: str) -> None:
        ...


class ScanningCacheStorage(Protocol):
    """Optional scanning interface for providers that support prefix scans."""

    def scan(self, prefix: str, limit: int = 1000) -> List[str]:
        ...

