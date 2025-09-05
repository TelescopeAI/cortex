from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from cortex.core.preaggregations.compute.postgres import PostgresComputeAdapter
from cortex.core.preaggregations.models import PreAggregationSpec, PreAggregationStatus
from cortex.api.schemas.requests.preaggregations import PreAggregationUpsertRequest
from cortex.api.schemas.responses.preaggregations import (
    PreAggregationUpsertResponse,
    PreAggregationListResponse,
    PreAggregationStatusResponse,
)
from cortex.core.preaggregations import get_service


PreAggregationsRouter = APIRouter()
_service = get_service()
if not any(getattr(a, "engine", None) and a.engine().value == PostgresComputeAdapter().engine().value for a in _service.compute_adapters):
    _service.compute_adapters.append(PostgresComputeAdapter())


@PreAggregationsRouter.post("/pre-aggregations", response_model=PreAggregationUpsertResponse, tags=["Pre Aggregations"])
def upsert_spec(payload: PreAggregationUpsertRequest) -> PreAggregationUpsertResponse:
    _service.upsert_spec(payload)
    return PreAggregationUpsertResponse(ok=True)


@PreAggregationsRouter.get("/pre-aggregations", response_model=PreAggregationListResponse, tags=["Pre Aggregations"])
def list_specs(metric_id: Optional[UUID] = None) -> PreAggregationListResponse:
    specs = _service.list_specs(metric_id=metric_id)
    return PreAggregationListResponse(specs=specs, total_count=len(specs))


@PreAggregationsRouter.get("/pre-aggregations/{spec_id}", response_model=PreAggregationSpec, tags=["Pre Aggregations"])
def get_spec(spec_id: str) -> PreAggregationSpec:
    spec = _service.get_spec(spec_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Pre-aggregation spec not found")
    return spec


@PreAggregationsRouter.post("/pre-aggregations/{spec_id}/refresh", response_model=PreAggregationStatusResponse, tags=["Pre Aggregations"])
def refresh_spec(spec_id: str, dry_run: bool = False) -> PreAggregationStatusResponse:
    return PreAggregationStatusResponse(status=_service.build_or_refresh(spec_id=spec_id, dry_run=dry_run))


@PreAggregationsRouter.get("/pre-aggregations/{spec_id}/status", response_model=PreAggregationStatusResponse, tags=["Pre Aggregations"])
def get_status(spec_id: str) -> PreAggregationStatusResponse:
    status = _service.get_status(spec_id)
    return PreAggregationStatusResponse(status=status or PreAggregationStatus(spec_id=spec_id, error="NO_STATUS"))


@PreAggregationsRouter.delete("/pre-aggregations/{spec_id}", tags=["Pre Aggregations"])
def delete_spec(spec_id: str) -> dict:
    success = _service.delete_spec(spec_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pre-aggregation spec not found")
    return {"ok": True}


