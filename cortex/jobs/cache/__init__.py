"""Cache management for SQLite databases

This module re-exports the cache manager from cortex.core.connectors.api.sheets
to maintain backward compatibility for jobs server usage.
"""
from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager

__all__ = ["CortexFileStorageCacheManager"]
