from typing import List, Optional

from cortex.core.preaggregations.models import (
    PreAggregationPlanResult,
    PreAggregationSpec,
    PreAggregationFilter,
)
from cortex.core.semantics.metrics.metric import SemanticMetric


class CoveragePreAggregationPlanner:
    def plan(
        self,
        metric: SemanticMetric,
        requested_dimensions: List[str],
        requested_measures: List[str],
        filters: Optional[List[PreAggregationFilter]] = None,
        specs: Optional[List[PreAggregationSpec]] = None,
    ) -> PreAggregationPlanResult:
        if not specs:
            return PreAggregationPlanResult(covered=False, reason="NO_SPECS")

        for spec in specs:
            if not self._covers_measures(spec, requested_measures):
                continue
            if not self._covers_dimensions(spec, requested_dimensions):
                continue
            if not self._filters_compatible(spec, filters or []):
                continue
            return PreAggregationPlanResult(covered=True, spec_id=spec.id)

        return PreAggregationPlanResult(covered=False, reason="NO_COVERING_SPEC")

    def _covers_measures(self, spec: PreAggregationSpec, measures: List[str]) -> bool:
        spec_measure_queries = [m.query for m in spec.measures if m.query]
        return set(measures).issubset(set(spec_measure_queries))

    def _covers_dimensions(self, spec: PreAggregationSpec, dims: List[str]) -> bool:
        spec_dimension_queries = [d.query for d in spec.dimensions if d.query]
        return set(dims).issubset(set(spec_dimension_queries))

    def _filters_compatible(self, spec: PreAggregationSpec, req_filters: List[PreAggregationFilter]) -> bool:
        # MVP: if spec defines pre-filters, request must include same column/op/value
        if not spec.filters:
            return True
        req_tuples = {(f.column, f.op, str(f.value)) for f in req_filters}
        spec_tuples = {(f.column, f.op, str(f.value)) for f in spec.filters}
        return spec_tuples.issubset(req_tuples)


