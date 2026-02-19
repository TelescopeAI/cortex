from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from cortex.core.preaggregations.models import PreAggregationSpec
from cortex.api.schemas.requests.preaggregations import PreAggregationUpsertRequest
from cortex.api.schemas.responses.preaggregations import (
    PreAggregationUpsertResponse,
    PreAggregationListResponse,
    PreAggregationStatusResponse,
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexSDKError


PreAggregationsRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@PreAggregationsRouter.post("/pre-aggregations", response_model=PreAggregationUpsertResponse, tags=["Pre Aggregations"])
def upsert_spec(payload: PreAggregationUpsertRequest) -> PreAggregationUpsertResponse:
    """Create or update a pre-aggregation spec"""
    try:
        return _client.preaggregations.upsert_preaggregation_spec(payload)
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@PreAggregationsRouter.get("/pre-aggregations", response_model=PreAggregationListResponse, tags=["Pre Aggregations"])
def list_specs(metric_id: Optional[UUID] = None) -> PreAggregationListResponse:
    """List pre-aggregation specs with optional metric filtering"""
    try:
        # Convert UUID to string for handler
        metric_id_str = str(metric_id) if metric_id else None
        return _client.preaggregations.list_preaggregation_specs(metric_id_str)
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@PreAggregationsRouter.get("/pre-aggregations/{spec_id}", response_model=PreAggregationSpec, tags=["Pre Aggregations"])
def get_spec(spec_id: str) -> PreAggregationSpec:
    """Get a pre-aggregation spec by ID"""
    try:
        return _client.preaggregations.get_preaggregation_spec(spec_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@PreAggregationsRouter.post("/pre-aggregations/{spec_id}/refresh", response_model=PreAggregationStatusResponse, tags=["Pre Aggregations"])
def refresh_spec(spec_id: str, dry_run: bool = False) -> PreAggregationStatusResponse:
    """Build or refresh a pre-aggregation spec"""
    try:
        return _client.preaggregations.refresh_preaggregation_spec(spec_id, dry_run)
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@PreAggregationsRouter.get("/pre-aggregations/{spec_id}/status", response_model=PreAggregationStatusResponse, tags=["Pre Aggregations"])
def get_status(spec_id: str) -> PreAggregationStatusResponse:
    """Get pre-aggregation spec status"""
    try:
        return _client.preaggregations.get_preaggregation_status(spec_id)
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


@PreAggregationsRouter.delete("/pre-aggregations/{spec_id}", tags=["Pre Aggregations"])
def delete_spec(spec_id: str) -> dict:
    """Delete a pre-aggregation spec"""
    try:
        return _client.preaggregations.delete_preaggregation_spec(spec_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=500, detail=str(e))


