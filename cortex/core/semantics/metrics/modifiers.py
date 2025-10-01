from typing import Optional, List, TypeVar, Protocol, Dict

from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.order_sequences import SemanticOrderSequence
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.metrics.metric import SemanticMetric


class MetricModifier(TSModel):
    """Upserts metric components; replaces matching items and appends new ones."""

    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None
    joins: Optional[List[SemanticJoin]] = None
    filters: Optional[List[SemanticFilter]] = None
    order: Optional[List[SemanticOrderSequence]] = None
    limit: Optional[int] = None


MetricModifiers = List[MetricModifier]


class _HasName(Protocol):
    name: str


TNamed = TypeVar("TNamed", bound=_HasName)


def _upsert_items(existing: Optional[List[TNamed]], incoming: Optional[List[TNamed]]) -> Optional[List[TNamed]]:
    """
    Upsert items by name. Replace items with the same name, append new ones.
    Returns a new list; does not mutate the input.
    """

    if not incoming:
        return existing

    current: List[TNamed] = list(existing) if existing else []
    index: Dict[str, int] = {item.name: i for i, item in enumerate(current)}

    for item in incoming:
        if item.name in index:
            current[index[item.name]] = item
        else:
            current.append(item)

    return current


def apply_metric_modifiers(metric: SemanticMetric, modifiers: Optional[MetricModifiers]) -> SemanticMetric:
    """
    Apply a list of metric modifiers to a metric, returning a deep-copied, modified metric.
    Aggregations are intentionally not handled.
    """

    if not modifiers:
        return metric

    resolved = metric.model_copy(deep=True)

    for modifier in modifiers:
        resolved.measures = _upsert_items(resolved.measures, modifier.measures)
        resolved.dimensions = _upsert_items(resolved.dimensions, modifier.dimensions)
        resolved.joins = _upsert_items(resolved.joins, modifier.joins)
        resolved.filters = _upsert_items(resolved.filters, modifier.filters)
        resolved.order = _upsert_items(resolved.order, modifier.order)

        if modifier.limit is not None:
            resolved.limit = modifier.limit

    return resolved


