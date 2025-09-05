from typing import Protocol

from cortex.core.preaggregations.models import EngineCapabilities, EngineType, PreAggregationSpec


class ResolverAdapter(Protocol):
    def id(self) -> str: ...

    def supports(self, source_engine: EngineType, dest_engine: EngineType, capabilities: EngineCapabilities) -> bool: ...

    def materialize(self, spec: PreAggregationSpec, select_sql: str) -> None: ...


