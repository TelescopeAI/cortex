"""
Pre-aggregations direct handler - Core service calls.

Handles pre-aggregation operations in Direct mode.
"""
from typing import Optional

from cortex.core.preaggregations import get_service
from cortex.core.preaggregations.compute.postgres import PostgresComputeAdapter
from cortex.core.preaggregations.models import PreAggregationSpec, PreAggregationStatus
from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest
from cortex.sdk.schemas.responses.preaggregations import (
    PreAggregationUpsertResponse,
    PreAggregationListResponse,
    PreAggregationStatusResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


# Initialize service with PostgreSQL adapter
_service = get_service()
if not any(
    getattr(a, "engine", None) and a.engine().value == PostgresComputeAdapter().engine().value
    for a in _service.compute_adapters
):
    _service.compute_adapters.append(PostgresComputeAdapter())


def upsert_preaggregation_spec(request: PreAggregationUpsertRequest) -> PreAggregationUpsertResponse:
    """
    Create or update a pre-aggregation spec - direct Core service call.

    Args:
        request: Pre-aggregation upsert request

    Returns:
        Upsert response
    """
    try:
        _service.upsert_spec(request)
        return PreAggregationUpsertResponse(ok=True)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_preaggregation_specs(metric_id: Optional[str] = None) -> PreAggregationListResponse:
    """
    List pre-aggregation specs - direct Core service call.

    Args:
        metric_id: Optional metric ID to filter by

    Returns:
        List of pre-aggregation specs
    """
    try:
        specs = _service.list_specs(metric_id=metric_id)
        return PreAggregationListResponse(specs=specs, total_count=len(specs))
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_preaggregation_spec(spec_id: str) -> PreAggregationSpec:
    """
    Get a pre-aggregation spec by ID - direct Core service call.

    Args:
        spec_id: Pre-aggregation spec ID

    Returns:
        Pre-aggregation spec
    """
    try:
        spec = _service.get_spec(spec_id)
        if not spec:
            raise CortexNotFoundError(f"Pre-aggregation spec with ID {spec_id} not found")
        return spec
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def refresh_preaggregation_spec(spec_id: str, dry_run: bool = False) -> PreAggregationStatusResponse:
    """
    Build or refresh a pre-aggregation spec - direct Core service call.

    Args:
        spec_id: Pre-aggregation spec ID
        dry_run: If True, only validate without building

    Returns:
        Status response
    """
    try:
        status = _service.build_or_refresh(spec_id=spec_id, dry_run=dry_run)
        return PreAggregationStatusResponse(status=status)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_preaggregation_status(spec_id: str) -> PreAggregationStatusResponse:
    """
    Get pre-aggregation spec status - direct Core service call.

    Args:
        spec_id: Pre-aggregation spec ID

    Returns:
        Status response
    """
    try:
        status = _service.get_status(spec_id)
        if not status:
            status = PreAggregationStatus(spec_id=spec_id, error="NO_STATUS")
        return PreAggregationStatusResponse(status=status)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_preaggregation_spec(spec_id: str) -> dict:
    """
    Delete a pre-aggregation spec - direct Core service call.

    Args:
        spec_id: Pre-aggregation spec ID

    Returns:
        Success message
    """
    try:
        success = _service.delete_spec(spec_id)
        if not success:
            raise CortexNotFoundError(f"Pre-aggregation spec with ID {spec_id} not found")
        return {"ok": True}
    except Exception as e:
        raise CoreExceptionMapper().map(e)
