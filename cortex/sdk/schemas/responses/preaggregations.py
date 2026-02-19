from typing import Optional

from cortex.core.types.telescope import TSModel
from cortex.core.preaggregations.models import PreAggregationSpec, PreAggregationStatus


class PreAggregationUpsertResponse(TSModel):
    ok: bool


class PreAggregationListResponse(TSModel):
    specs: list[PreAggregationSpec]
    total_count: int


class PreAggregationStatusResponse(TSModel):
    status: PreAggregationStatus


