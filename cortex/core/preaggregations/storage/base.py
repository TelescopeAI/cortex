from typing import Protocol

from cortex.core.preaggregations.models import PreAggregationSpec


class StorageAdapter(Protocol):
    def resolve_location(self, spec: PreAggregationSpec) -> str: ...


