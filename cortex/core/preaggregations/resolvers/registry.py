from typing import Dict, Iterable, Optional

from cortex.core.preaggregations.models import EngineCapabilities, EngineType
from cortex.core.preaggregations.resolvers.base import ResolverAdapter


class ResolverRegistry:
    def __init__(self) -> None:
        self._resolvers: Dict[str, ResolverAdapter] = {}

    def register(self, resolver: ResolverAdapter) -> None:
        self._resolvers[resolver.id()] = resolver

    def get(self, resolver_id: str) -> Optional[ResolverAdapter]:
        return self._resolvers.get(resolver_id)

    def pick_supported(self, source_engine: EngineType, dest_engine: EngineType, capabilities: EngineCapabilities) -> Optional[ResolverAdapter]:
        for resolver in self._resolvers.values():
            if resolver.supports(source_engine, dest_engine, capabilities):
                return resolver
        return None

    def list_all(self) -> Iterable[ResolverAdapter]:
        return list(self._resolvers.values())


