from typing import Dict, Iterable, Optional, List
from abc import ABC, abstractmethod
from uuid import UUID

from cortex.core.preaggregations.models import PreAggregationSpec


class PreAggregationRegistry(ABC):
    """Abstract registry for storing and retrieving PreAggregationSpec objects.

    Concrete implementations may back this with an in-memory map, a database table,
    or a remote key-value store. The registry is responsible for CRUD on specs and
    efficient listing by metric.
    """

    @abstractmethod
    def upsert_spec(self, spec: PreAggregationSpec) -> None:
        """Create or update a pre-aggregation spec by id."""
        raise NotImplementedError

    @abstractmethod
    def get_spec(self, spec_id: str) -> Optional[PreAggregationSpec]:
        """Retrieve a pre-aggregation spec by id, or None if missing."""
        raise NotImplementedError

    @abstractmethod
    def list_specs(self, metric_id: Optional[UUID] = None) -> Iterable[PreAggregationSpec]:
        """List specs, optionally filtering by metric id."""
        raise NotImplementedError

    @abstractmethod
    def delete_spec(self, spec_id: str) -> None:
        """Delete a spec by id. No-op if it does not exist."""
        raise NotImplementedError


class InMemoryPreAggregationRegistry(PreAggregationRegistry):
    """Simple in-memory registry implementation for development and tests."""

    def __init__(self) -> None:
        self._specs_by_id: Dict[str, PreAggregationSpec] = {}
        self._spec_ids_by_metric: Dict[UUID, List[str]] = {}

    def upsert_spec(self, spec: PreAggregationSpec) -> None:
        self._specs_by_id[spec.id] = spec
        metric_list = self._spec_ids_by_metric.setdefault(spec.metric_id, [])
        if spec.id not in metric_list:
            metric_list.append(spec.id)

    def get_spec(self, spec_id: str) -> Optional[PreAggregationSpec]:
        return self._specs_by_id.get(spec_id)

    def list_specs(self, metric_id: Optional[UUID] = None) -> Iterable[PreAggregationSpec]:
        if metric_id is None:
            return list(self._specs_by_id.values())
        ids = self._spec_ids_by_metric.get(metric_id, [])
        return [self._specs_by_id[i] for i in ids if i in self._specs_by_id]

    def delete_spec(self, spec_id: str) -> None:
        spec = self._specs_by_id.pop(spec_id, None)
        if spec is None:
            return
        ids = self._spec_ids_by_metric.get(spec.metric_id, [])
        if spec_id in ids:
            ids.remove(spec_id)


