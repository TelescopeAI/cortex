from cortex.core.preaggregations.models import PreAggregationSpec
from cortex.core.preaggregations.storage.base import StorageAdapter


class SourceStorageAdapter(StorageAdapter):
    def resolve_location(self, spec: PreAggregationSpec) -> str:
        # For source mode, use the source table schema with a derived name
        base = spec.name or f"mv_{spec.metric_id}"
        return base


