"""
Direct mode implementations for metrics operations.

Calls Core services directly for local operations.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.storage.store import CortexStorage
from cortex.core.services.metrics.execution import MetricExecutionService, MetricsGenerationService
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.types.databases import DataSourceTypes
from cortex.core.utils.schema_inference import auto_infer_semantic_types
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError, CortexValidationError
from cortex.sdk.schemas.requests.metrics import (
    MetricCreateRequest,
    MetricUpdateRequest,
    MetricExecutionRequest,
    MetricCloneRequest,
    MetricVersionCreateRequest,
    MetricRecommendationsRequest,
)
from cortex.sdk.schemas.responses.metrics import (
    MetricResponse,
    MetricListResponse,
    MetricExecutionResponse,
    MetricVersionResponse,
    MetricVersionListResponse,
    MetricRecommendationsResponse,
)
from cortex.core.doctor.chief import CortexDoctor
from cortex.sdk.schemas.responses.doctor import DiagnoseResponse

logger = logging.getLogger(__name__)


def _build_metric_updates(metric_data_dict: dict, db_metric) -> dict:
    """
    Build updates dictionary by comparing incoming data with database values.
    Properly handles empty arrays and None values.

    Args:
        metric_data_dict: Dictionary of new values from the request
        db_metric: Existing metric from database

    Returns:
        Dictionary of fields to update
    """
    updates = {}

    for key, new_value in metric_data_dict.items():
        # Skip fields that shouldn't be updated
        if key in ['id', 'data_model_id', 'created_at', 'updated_at', 'version']:
            continue

        # Get current database value
        current_value = getattr(db_metric, key, None)

        # Handle different field types
        if key in ['measures', 'dimensions', 'filters', 'joins', 'order', 'aggregations']:
            # For arrays, always update if the key is present in the request
            # This handles empty arrays correctly ([] is a valid update)
            if key in metric_data_dict:
                updates[key] = new_value

        elif key in ['limit', 'filters']:
            # These fields can be explicitly set to None/empty
            if new_value is not None or key in ['limit', 'filters']:
                updates[key] = new_value

        elif key in ['name', 'alias', 'title', 'description', 'query', 'table_name',
                     'data_source_id', 'parameters', 'refresh', 'cache', 'meta']:
            # For other fields, only update if value is different
            if new_value != current_value:
                updates[key] = new_value

        elif key in ['grouped', 'ordered', 'public']:
            # For boolean fields, only update if value is different and not None
            if new_value is not None and new_value != current_value:
                updates[key] = new_value

        else:
            # For any other fields, update if value is not None
            if new_value is not None:
                updates[key] = new_value

    return updates


def list_metrics(
    environment_id: UUID,
    page: int = 1,
    page_size: int = 20,
    data_model_id: Optional[UUID] = None,
    public_only: Optional[bool] = None,
    valid_only: Optional[bool] = None
) -> MetricListResponse:
    """
    List metrics in an environment - direct Core service call.

    Args:
        environment_id: Environment ID
        page: Page number (1-indexed)
        page_size: Number of items per page
        data_model_id: Optional filter by data model ID
        public_only: Optional filter by public status
        valid_only: Optional filter by valid status

    Returns:
        MetricListResponse with list of metrics

    Raises:
        CortexValidationError: If environment_id is invalid
        CortexSDKError: On other errors
    """
    metric_service = MetricService()
    try:
        skip = (page - 1) * page_size
        db_metrics = metric_service.get_all_metrics(
            environment_id=environment_id,
            skip=skip,
            limit=page_size,
            data_model_id=data_model_id,
            public_only=public_only,
            valid_only=valid_only
        )

        # Convert to response format with data model names
        metrics = []
        model_service = DataModelService()
        try:
            for db_metric in db_metrics:
                # Convert ORM to Pydantic
                pydantic_metric = SemanticMetric.model_validate(db_metric, from_attributes=True)
                data_model = model_service.get_data_model_by_id(pydantic_metric.data_model_id)
                data_model_name = data_model.name if data_model else "Unknown"

                metrics.append(MetricResponse(
                    **pydantic_metric.model_dump(),
                    data_model_name=data_model_name
                ))
        finally:
            model_service.close()

        total_count = len(metrics)  # In production, do separate count query

        return MetricListResponse(
            metrics=metrics,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        metric_service.close()


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
    service = MetricService()
    try:
        metric = service.get_metric_by_id(metric_id)

        if not metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        return MetricResponse.model_validate(metric, from_attributes=True)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


def create_metric(request: MetricCreateRequest) -> MetricResponse:
    """
    Create a new metric - direct Core service call.

    Includes schema inference for measures, dimensions, and filters.

    Args:
        request: Metric creation request

    Returns:
        MetricResponse

    Raises:
        CortexValidationError: If validation fails
    """
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

        # Auto-infer source_type and source_meta for measures, dimensions, and filters
        measures = request.measures
        dimensions = request.dimensions
        filters = request.filters

        if request.data_source_id and (measures or dimensions or filters):
            try:
                # Get data source schema for auto-inference
                data_source = DataSourceCRUD.get_data_source(request.data_source_id)
                config = data_source.config

                # Add dialect for SQL databases if not present
                if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL,
                                                 DataSourceTypes.ORACLE, DataSourceTypes.SQLITE,
                                                 DataSourceTypes.SPREADSHEET]:
                    config["dialect"] = data_source.source_type

                # Create database client and get schema
                client = DBClientService.get_client(details=config, db_type=data_source.source_type)
                client.connect()
                schema = client.get_schema()

                # Auto-infer source types and metadata
                inferred_measures, inferred_dimensions, inferred_filters = auto_infer_semantic_types(
                    measures, dimensions, filters, schema
                )

                # Use inferred values if available, otherwise keep original
                measures = inferred_measures if inferred_measures is not None else measures
                dimensions = inferred_dimensions if inferred_dimensions is not None else dimensions
                filters = inferred_filters if inferred_filters is not None else filters

            except Exception as e:
                # Schema inference failed, but continue with metric creation
                logger.warning(f"Schema inference failed for metric {request.name}: {str(e)}")

        # Create metric with environment_id and potentially updated measures/dimensions/filters
        metric_service = MetricService()
        metric_data = request.model_dump()
        metric_data["environment_id"] = environment_id
        # Update with inferred values
        metric_data["measures"] = measures
        metric_data["dimensions"] = dimensions
        metric_data["filters"] = filters

        metric = metric_service.create_metric(SemanticMetric(**metric_data))
        # Build response with data model name
        response = MetricResponse.model_validate(metric, from_attributes=True)
        response.data_model_name = data_model.name

        return response

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        model_service.close()
        metric_service.close()


def update_metric(metric_id: UUID, request: MetricUpdateRequest) -> MetricResponse:
    """
    Update a metric - direct Core service call.

    Includes schema inference for measures, dimensions, and filters.

    Args:
        metric_id: Metric ID
        request: Metric update request

    Returns:
        MetricResponse

    Raises:
        CortexNotFoundError: If metric doesn't exist
        CortexValidationError: If validation fails
    """
    try:
        service = MetricService()

        # Get existing metric and validate environment
        db_metric = service.get_metric_by_id(metric_id, environment_id=request.environment_id)
        if not db_metric:
            raise CortexNotFoundError(
                f"Metric with ID {metric_id} not found in environment {request.environment_id}"
            )

        # Auto-infer source_type and source_meta for updated measures, dimensions, and filters
        metric_data_dict = request.model_dump()

        # Only perform schema inference if measures, dimensions, or filters are being updated
        if any(key in metric_data_dict and metric_data_dict[key] is not None
               for key in ['measures', 'dimensions', 'filters']):

            # Get the data_source_id (either from update or existing metric)
            data_source_id = metric_data_dict.get('data_source_id') or db_metric.data_source_id

            if data_source_id:
                try:
                    # Get data source schema for auto-inference
                    data_source = DataSourceCRUD.get_data_source(data_source_id)
                    config = data_source.config

                    # Add dialect for SQL databases if not present
                    if data_source.source_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL,
                                                     DataSourceTypes.ORACLE, DataSourceTypes.SQLITE,
                                                     DataSourceTypes.SPREADSHEET]:
                        config["dialect"] = data_source.source_type

                    # Create database client and get schema
                    client = DBClientService.get_client(details=config, db_type=data_source.source_type)
                    client.connect()
                    schema = client.get_schema()

                    # Get current or updated values
                    # Use 'in' check to properly handle empty arrays (which are falsy but valid)
                    measures_data = metric_data_dict['measures'] if 'measures' in metric_data_dict else db_metric.measures
                    dimensions_data = metric_data_dict['dimensions'] if 'dimensions' in metric_data_dict else db_metric.dimensions
                    filters_data = metric_data_dict['filters'] if 'filters' in metric_data_dict else db_metric.filters

                    # Convert dicts to Pydantic models for inference
                    measures = None
                    dimensions = None
                    filters = None

                    if measures_data:
                        measures = [SemanticMeasure.model_validate(m) if isinstance(m, dict) else m for m in measures_data]
                    if dimensions_data:
                        dimensions = [SemanticDimension.model_validate(d) if isinstance(d, dict) else d for d in dimensions_data]
                    if filters_data:
                        filters = [SemanticFilter.model_validate(f) if isinstance(f, dict) else f for f in filters_data]

                    # Auto-infer source types and metadata
                    inferred_measures, inferred_dimensions, inferred_filters = auto_infer_semantic_types(
                        measures, dimensions, filters, schema
                    )

                    # Update the metric_data_dict with inferred values (convert back to dicts for JSONB)
                    if 'measures' in metric_data_dict and metric_data_dict['measures'] is not None:
                        metric_data_dict['measures'] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in inferred_measures] if inferred_measures else None
                    if 'dimensions' in metric_data_dict and metric_data_dict['dimensions'] is not None:
                        metric_data_dict['dimensions'] = [d.model_dump() if hasattr(d, 'model_dump') else d for d in inferred_dimensions] if inferred_dimensions else None
                    if 'filters' in metric_data_dict and metric_data_dict['filters'] is not None:
                        metric_data_dict['filters'] = [f.model_dump() if hasattr(f, 'model_dump') else f for f in inferred_filters] if inferred_filters else None

                except Exception as e:
                    # Schema inference failed, but continue with metric update
                    logger.warning(f"Schema inference failed for metric update {metric_id}: {str(e)}")

        # Update metric
        # Build updates by comparing with database values
        updates = _build_metric_updates(metric_data_dict, db_metric)
        updated_metric = service.update_metric(metric_id, updates)

        if not updated_metric:
            raise CortexNotFoundError(f"Metric with ID {metric_id} not found")
        # Build response with data model name
        response = MetricResponse.model_validate(updated_metric, from_attributes=True)

        # Get data model name
        model_service = DataModelService()
        try:
            data_model = model_service.get_data_model_by_id(response.data_model_id)
            if data_model:
                response.data_model_name = data_model.name
        finally:
            model_service.close()

        return response

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


def delete_metric(metric_id: UUID, environment_id: Optional[UUID] = None) -> None:
    """
    Delete a metric - direct Core service call.

    Args:
        metric_id: Metric ID
        environment_id: Optional environment ID

    Raises:
        CortexNotFoundError: If metric doesn't exist
    """
    try:
        service = MetricService()

        # Verify metric exists
        metric = service.get_metric_by_id(metric_id)
        if not metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        # Delete metric
        service.delete_metric(metric_id)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


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
    try:
        service = MetricService()

        # Get source metric
        source_metric = service.get_metric_by_id(metric_id)
        if not source_metric:
            raise CortexNotFoundError(f"Metric {metric_id} not found")

        # Clone metric
        cloned_metric = service.clone_metric(metric_id, request.new_name)
        return MetricResponse.model_validate(cloned_metric, from_attributes=True)
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


def list_metric_versions(metric_id: UUID) -> MetricVersionListResponse:
    """
    List all versions of a metric - direct Core service call.

    Args:
        metric_id: Metric ID

    Returns:
        MetricVersionListResponse with list of versions

    Raises:
        CortexNotFoundError: If metric doesn't exist
    """
    try:
        service = MetricService()

        # Check if metric exists
        db_metric = service.get_metric_by_id(metric_id)
        if not db_metric:
            raise CortexNotFoundError(f"Metric with ID {metric_id} not found")

        # Get versions
        db_versions = service.get_metric_versions(metric_id)

        versions = []
        for db_version in db_versions:
            versions.append(MetricVersionResponse(
                id=db_version.id,
                metric_id=db_version.metric_id,
                version_number=db_version.version_number,
                snapshot_data=db_version.snapshot_data,
                description=db_version.description,
                created_by=db_version.created_by,
                tags=db_version.tags,
                created_at=db_version.created_at
            ))

        return MetricVersionListResponse(
            versions=versions,
            total_count=len(versions)
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


def create_metric_version(
    metric_id: UUID,
    request: MetricVersionCreateRequest
) -> MetricVersionResponse:
    """
    Create a new version of a metric - direct Core service call.

    Args:
        metric_id: Metric ID
        request: Version creation request

    Returns:
        MetricVersionResponse

    Raises:
        CortexNotFoundError: If metric doesn't exist
        CortexValidationError: If validation fails
    """
    try:
        service = MetricService()

        # Create version
        db_version = service.create_metric_version(metric_id, request.description)
        return MetricVersionResponse(
            id=db_version.id,
            metric_id=db_version.metric_id,
            version_number=db_version.version_number,
            snapshot_data=db_version.snapshot_data,
            description=db_version.description,
            created_by=db_version.created_by,
            tags=db_version.tags,
            created_at=db_version.created_at
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        service.close()


def generate_metric_recommendations(
    request: MetricRecommendationsRequest
) -> MetricRecommendationsResponse:
    """
    Generate metric recommendations from a data source schema - direct Core service call.

    This analyzes the schema of a data source and generates a set of recommended
    metrics based on deterministic rules. The generated metrics are not saved.

    Args:
        request: Recommendations request

    Returns:
        MetricRecommendationsResponse with generated metrics

    Raises:
        CortexNotFoundError: If resources not found
        CortexValidationError: If validation fails
    """
    model_service = None
    try:
        # Generate metrics using the service
        generated_metrics = MetricsGenerationService.generate_metrics(
            environment_id=request.environment_id,
            data_source_id=request.data_source_id,
            data_model_id=request.data_model_id,
            select=request.select,
            metric_types=request.metric_types,
            time_windows=request.time_windows,
            grains=request.grains,
        )

        # Convert to response format
        metric_responses = []
        table_preview = {}
        model_service = DataModelService()

        data_model = model_service.get_data_model_by_id(request.data_model_id)
        data_model_name = data_model.name if data_model else "Unknown"

        for metric in generated_metrics:
            metric_responses.append(MetricResponse(
                **metric.model_dump(),
                data_model_name=data_model_name
            ))
            table_key = getattr(metric, "table_name", None)
            if table_key:
                entry = table_preview.setdefault(table_key, {"count": 0, "metric_names": []})
                entry["count"] += 1
                entry["metric_names"].append(metric.name)

        return MetricRecommendationsResponse(
            metrics=metric_responses,
            total_count=len(metric_responses),
            metadata={
                "environment_id": str(request.environment_id),
                "data_source_id": str(request.data_source_id),
                "data_model_id": str(request.data_model_id),
                "select": request.select.model_dump() if request.select else {},
                "metric_types": request.metric_types,
                "time_windows": request.time_windows,
                "grains": request.grains,
                "table_preview": table_preview,
            }
        )

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        if model_service is not None:
            model_service.close()


def diagnose_metric(request) -> "DiagnoseResponse":
    """
    Diagnose a metric - direct Core service call.

    Args:
        request: MetricDiagnoseRequest with metric_id or inline metric

    Returns:
        DiagnoseResponse with diagnosis result
    """
    try:
        result = CortexDoctor.diagnose_metric(
            metric_id=request.metric_id,
            metric=request.metric,
            environment_id=request.environment_id,
        )
        return DiagnoseResponse(
            healthy=result.healthy,
            diagnosis=result.diagnosis,
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)
