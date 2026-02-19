"""
Direct mode implementations for metrics operations.

Calls Core services directly for local operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.storage.store import CortexStorage
from cortex.core.services.metrics.execution import MetricExecutionService
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError, CortexValidationError
from cortex.sdk.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
)
from cortex.sdk.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
)

logger = logging.getLogger(__name__)


def list_metrics(
    environment_id: UUID, limit: int = 100, offset: int = 0, **filters
) -> MetricListResponse:
    """
    List metrics in an environment - direct Core service call.

    Args:
        environment_id: Environment ID
        limit: Page size
        offset: Page offset
        **filters: Additional filters

    Returns:
        MetricListResponse with list of metrics

    Raises:
        CortexValidationError: If environment_id is invalid
        CortexSDKError: On other errors
    """
    db_session = CortexStorage().get_session()
    try:
        service = MetricService(db_session=db_session)
        metrics = service.list_metrics_by_environment(
            environment_id=environment_id, limit=limit, offset=offset
        )
        db_session.commit()

        return MetricListResponse(
            metrics=[MetricResponse.model_validate(m.to_dict()) for m in metrics],
            total=len(metrics),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()


def get_metric(metric_id: UUID, environment_id: Optional[UUID] = None) -> MetricResponse:
    """
    Get metric by ID - direct Core service call.

    Args:
        metric_id: Metric ID
        environment_id: Optional environment ID

    Returns:
        MetricResponse

    Raises:
        CortexNotFoundError: If metric doesn't exist
    """
    db_session = CortexStorage().get_session()
    try:
        service = MetricService(db_session=db_session)
        metric = service.get_metric_by_id(metric_id)

        if not metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        db_session.commit()
        return MetricResponse.model_validate(metric.to_dict())
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()


def create_metric(request: MetricCreateRequest) -> MetricResponse:
    """
    Create a new metric - direct Core service call.

    Args:
        request: Metric creation request

    Returns:
        MetricResponse

    Raises:
        CortexValidationError: If validation fails
    """
    db_session = CortexStorage().get_session()
    try:
        # Verify data model exists
        model_service = DataModelService()
        data_model = model_service.get_data_model_by_id(request.data_model_id)
        if not data_model:
            raise CortexNotFoundError(
                f"Data model with ID {request.data_model_id} not found"
            )

        # Get environment_id from data model
        environment_id = data_model.environment_id

        # Create metric with environment_id
        metric_service = MetricService(db_session=db_session)
        metric_data = request.model_dump()
        metric_data["environment_id"] = environment_id

        metric = metric_service.create_metric(metric_data)
        db_session.commit()

        return MetricResponse.model_validate(metric.to_dict())
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()


def update_metric(metric_id: UUID, request: MetricUpdateRequest) -> MetricResponse:
    """
    Update a metric - direct Core service call.

    Args:
        metric_id: Metric ID
        request: Metric update request

    Returns:
        MetricResponse

    Raises:
        CortexNotFoundError: If metric doesn't exist
        CortexValidationError: If validation fails
    """
    db_session = CortexStorage().get_session()
    try:
        service = MetricService(db_session=db_session)

        # Get existing metric
        metric = service.get_metric_by_id(metric_id)
        if not metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        # Build updates (only include fields that were provided)
        updates = request.model_dump(exclude_unset=True)

        # Update metric
        updated_metric = service.update_metric(metric_id, updates)
        db_session.commit()

        return MetricResponse.model_validate(updated_metric.to_dict())
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()


def delete_metric(metric_id: UUID, environment_id: Optional[UUID] = None) -> None:
    """
    Delete a metric - direct Core service call.

    Args:
        metric_id: Metric ID
        environment_id: Optional environment ID

    Raises:
        CortexNotFoundError: If metric doesn't exist
    """
    db_session = CortexStorage().get_session()
    try:
        service = MetricService(db_session=db_session)

        # Verify metric exists
        metric = service.get_metric_by_id(metric_id)
        if not metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        # Delete metric
        service.delete_metric(metric_id)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()


def execute_metric(
    metric_id: UUID, request: MetricExecutionRequest
) -> MetricExecutionResponse:
    """
    Execute a metric query - direct Core service call.

    Args:
        metric_id: Metric ID
        request: Execution request with parameters

    Returns:
        MetricExecutionResponse with query results

    Raises:
        CortexNotFoundError: If metric doesn't exist
    """
    try:
        result = MetricExecutionService.execute_metric(
            metric_id=metric_id,
            context_id=request.context_id,
            parameters=request.parameters or {},
            limit=request.limit,
            offset=request.offset,
            grouped=request.grouped,
            cache_preference=request.cache,
            modifiers=request.modifiers,
            preview=request.preview,
        )

        return MetricExecutionResponse(
            success=result.get("success", True),
            data=result.get("data"),
            metadata=result.get("metadata", {}),
            errors=result.get("errors"),
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def clone_metric(metric_id: UUID, request: MetricCloneRequest) -> MetricResponse:
    """
    Clone a metric with a new name - direct Core service call.

    Args:
        metric_id: Source metric ID
        request: Clone request with new name

    Returns:
        MetricResponse for cloned metric

    Raises:
        CortexNotFoundError: If source metric doesn't exist
    """
    db_session = CortexStorage().get_session()
    try:
        service = MetricService(db_session=db_session)

        # Get source metric
        source_metric = service.get_metric_by_id(metric_id)
        if not source_metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        # Clone metric
        cloned_metric = service.clone_metric(metric_id, request.new_name)
        db_session.commit()

        return MetricResponse.model_validate(cloned_metric.to_dict())
    except Exception as e:
        db_session.rollback()
        raise CoreExceptionMapper().map(e)
    finally:
        db_session.close()
