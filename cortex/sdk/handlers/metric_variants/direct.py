"""
Metric variants direct handler - Core service calls.

Handles metric variant operations in Direct mode.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.metric_variant_service import MetricVariantService
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.compiler import compile as compile_metric
from cortex.core.services.metrics.execution import MetricExecutionService
from cortex.sdk.schemas.requests.variants import (
    MetricVariantCreateRequest,
    MetricVariantUpdateRequest,
    MetricVariantExecutionRequest
)
from cortex.sdk.schemas.responses.variants import (
    MetricVariantResponse,
    MetricVariantListResponse,
    MetricVariantExecutionResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_variant(request: MetricVariantCreateRequest) -> MetricVariantResponse:
    """
    Create a new metric variant - direct Core service call.

    Args:
        request: Metric variant creation request

    Returns:
        Created metric variant response
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        # Verify source metric exists and belongs to the environment
        source_metric_id = request.source.metric_id
        if not source_metric_id:
            raise ValueError("Source metric_id is required")

        source_metric = metric_service.get_metric_by_id(
            source_metric_id,
            environment_id=request.environment_id
        )
        if not source_metric:
            raise CortexNotFoundError(
                f"Source metric with ID {source_metric_id} not found in environment {request.environment_id}"
            )

        # Create variant model with explicit environment/data_model/data_source binding
        variant = SemanticMetricVariant(
            name=request.name,
            alias=request.alias,
            description=request.description,
            environment_id=request.environment_id,
            data_model_id=source_metric.data_model_id,
            data_source_id=source_metric.data_source_id,
            source_id=source_metric_id,
            source=request.source,
            overrides=request.overrides,
            include=request.include,
            derivations=request.derivations,
            combine=request.combine,
            public=request.public,
            cache=request.cache,
            refresh=request.refresh,
            parameters=request.parameters,
            meta=request.meta
        )

        # Create via MetricVariantService
        db_variant = variant_service.create_variant(variant)

        # Convert to response
        response = MetricVariantResponse.model_validate(db_variant)

        # Add source metric name
        response.source_metric_name = source_metric.name

        return response

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def list_variants(
    environment_id: UUID,
    data_model_id: Optional[UUID] = None,
    source_metric_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> MetricVariantListResponse:
    """
    List metric variants - direct Core service call.

    Args:
        environment_id: Environment ID
        data_model_id: Optional data model ID filter
        source_metric_id: Optional source metric ID filter
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of metric variant responses
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        # Get variants using MetricVariantService
        variants = variant_service.get_all_variants(
            environment_id=environment_id,
            data_model_id=data_model_id,
            source_metric_id=source_metric_id,
            skip=offset,
            limit=limit
        )

        # Convert to response models
        variant_responses = []
        for v in variants:
            response = MetricVariantResponse.model_validate(v)
            # Optionally add source metric name
            if hasattr(v, "source") and v.source and hasattr(v.source, "get") and v.source.get("metric_id"):
                try:
                    source_metric = metric_service.get_metric_by_id(UUID(v.source["metric_id"]))
                    if source_metric:
                        response.source_metric_name = source_metric.name
                except:
                    pass
            variant_responses.append(response)

        return MetricVariantListResponse(
            variants=variant_responses,
            total_count=len(variant_responses),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def get_variant(variant_id: UUID, environment_id: UUID) -> MetricVariantResponse:
    """
    Get a metric variant by ID - direct Core service call.

    Args:
        variant_id: Variant ID
        environment_id: Environment ID

    Returns:
        Metric variant response
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        db_variant = variant_service.get_variant_by_id(variant_id, environment_id=environment_id)
        if not db_variant:
            raise CortexNotFoundError(
                f"Variant with ID {variant_id} not found in environment {environment_id}"
            )

        # Convert to response
        response = MetricVariantResponse.model_validate(db_variant)

        # Optionally add source metric name
        if hasattr(db_variant, "source") and db_variant.source and hasattr(db_variant.source, "get") and db_variant.source.get("metric_id"):
            try:
                source_metric = metric_service.get_metric_by_id(UUID(db_variant.source["metric_id"]))
                if source_metric:
                    response.source_metric_name = source_metric.name
            except:
                pass

        return response

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def update_variant(
    variant_id: UUID,
    request: MetricVariantUpdateRequest
) -> MetricVariantResponse:
    """
    Update a metric variant - direct Core service call.

    Args:
        variant_id: Variant ID
        request: Update request

    Returns:
        Updated metric variant response
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        # Get existing variant and validate environment
        db_variant = variant_service.get_variant_by_id(variant_id, environment_id=request.environment_id)
        if not db_variant:
            raise CortexNotFoundError(
                f"Variant with ID {variant_id} not found in environment {request.environment_id}"
            )

        # Build updates dictionary directly from request fields (only non-None values)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.alias is not None:
            updates["alias"] = request.alias
        if request.description is not None:
            updates["description"] = request.description
        if request.source is not None:
            updates["source"] = request.source.model_dump() if hasattr(request.source, 'model_dump') else request.source
        if request.overrides is not None:
            updates["overrides"] = request.overrides.model_dump() if hasattr(request.overrides, 'model_dump') else request.overrides
        if request.include is not None:
            updates["include"] = request.include.model_dump() if hasattr(request.include, 'model_dump') else request.include
        if request.derivations is not None:
            updates["derivations"] = [d.model_dump() for d in request.derivations] if request.derivations else None
        if request.combine is not None:
            updates["combine"] = [c.model_dump() for c in request.combine] if request.combine else None
        if request.public is not None:
            updates["public"] = request.public
        if request.cache is not None:
            updates["cache"] = request.cache.model_dump() if hasattr(request.cache, 'model_dump') else request.cache
        if request.refresh is not None:
            updates["refresh"] = request.refresh.model_dump() if hasattr(request.refresh, 'model_dump') else request.refresh
        if request.parameters is not None:
            updates["parameters"] = {k: v.model_dump() for k, v in request.parameters.items()} if request.parameters else None
        if request.meta is not None:
            updates["meta"] = request.meta

        # Update variant in database
        updated_variant = variant_service.update_variant(variant_id, updates)

        # Convert to response
        response = MetricVariantResponse.model_validate(updated_variant)

        # Optionally add source metric name
        if hasattr(updated_variant, "source") and updated_variant.source and hasattr(updated_variant.source, "get") and updated_variant.source.get("metric_id"):
            try:
                source_metric = metric_service.get_metric_by_id(UUID(updated_variant.source["metric_id"]))
                if source_metric:
                    response.source_metric_name = source_metric.name
            except:
                pass

        return response

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def delete_variant(variant_id: UUID, environment_id: UUID) -> None:
    """
    Delete a metric variant - direct Core service call.

    Args:
        variant_id: Variant ID
        environment_id: Environment ID
    """
    variant_service = MetricVariantService()

    try:
        # Get existing variant and validate environment
        db_variant = variant_service.get_variant_by_id(variant_id, environment_id=environment_id)
        if not db_variant:
            raise CortexNotFoundError(
                f"Variant with ID {variant_id} not found in environment {environment_id}"
            )

        # Delete variant (cascades to versions)
        variant_service.delete_variant(variant_id)

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()


def reset_variant(variant_id: UUID) -> Dict[str, Any]:
    """
    Reset a variant by removing all overrides - direct Core service call.

    Args:
        variant_id: Variant ID

    Returns:
        Reset result dictionary
    """
    variant_service = MetricVariantService()

    try:
        # Get existing variant
        db_variant = variant_service.get_variant_by_id(variant_id)
        if not db_variant:
            raise CortexNotFoundError(f"Variant with ID {variant_id} not found")

        # Reset overrides
        updates = {
            "overrides": None,
            "include": None,
            "derivations": None,
            "combine": None,
        }

        updated_variant = variant_service.update_variant(variant_id, updates)

        return {
            "success": True,
            "data": updated_variant,
            "message": "Variant reset successfully",
        }

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()


def detach_variant(variant_id: UUID) -> Dict[str, Any]:
    """
    Detach a variant by creating a new standalone metric - direct Core service call.

    Args:
        variant_id: Variant ID

    Returns:
        Detach result dictionary with new metric ID
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        # Get existing variant
        db_variant = variant_service.get_variant_by_id(variant_id)
        if not db_variant:
            raise CortexNotFoundError(f"Variant with ID {variant_id} not found")

        # Deserialize as variant
        variant = SemanticMetricVariant.model_validate(db_variant, from_attributes=True)

        # Create fetcher for compiler
        def fetcher(mid: UUID):
            # Try to get from variant service first
            db_v = variant_service.get_variant_by_id(mid)
            if db_v:
                return SemanticMetricVariant.model_validate(db_v, from_attributes=True)
            # Otherwise get from metric service
            db_m = metric_service.get_metric_by_id(mid)
            if not db_m:
                raise ValueError(f"Metric with ID {mid} not found")
            return SemanticMetric.model_validate(db_m, from_attributes=True)

        # Compile variant to resolved metric
        resolved_metric = compile_metric(variant, fetcher)

        # Create new standalone metric
        new_metric_dict = resolved_metric.model_dump()
        new_metric_dict["name"] = f"{resolved_metric.name}_detached"
        new_metric_dict.pop("id", None)  # Let DB generate new ID

        new_metric = metric_service.create_metric(new_metric_dict)

        return {
            "success": True,
            "data": new_metric,
            "message": f"Variant detached as new metric: {new_metric.id}",
        }

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def execute_variant(
    request: MetricVariantExecutionRequest
) -> MetricVariantExecutionResponse:
    """
    Execute a metric variant - direct Core service call.

    Supports two modes:
    - By ID: request.variant_id is set — fetches saved variant from DB
    - Inline: request.variant is set — constructs in-memory variant for preview without saving

    Args:
        request: Execution request (must have either variant_id or variant)

    Returns:
        Execution response with results
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()
    execution_service = MetricExecutionService()

    try:
        if request.variant_id is not None:
            # Mode 1: Execute a saved variant by ID
            db_variant = variant_service.get_variant_by_id(
                request.variant_id, environment_id=request.environment_id
            )
            if not db_variant:
                raise CortexNotFoundError(
                    f"Variant with ID {request.variant_id} not found in environment {request.environment_id}"
                )

            result = execution_service.execute_metric(
                metric_id=str(request.variant_id),
                context_id=request.context_id,
                parameters=request.parameters,
                limit=request.limit,
                offset=request.offset,
                grouped=request.grouped,
                cache_preference=request.cache,
                preview=request.preview,
            )
        else:
            # Mode 2: Execute an inline variant definition (preview without saving)
            inline = request.variant

            # Fetch source metric to get data_model_id and data_source_id
            source_metric_id = inline.source.metric_id
            if not source_metric_id:
                raise ValueError("Source metric_id is required in inline variant definition")

            source_metric = metric_service.get_metric_by_id(
                source_metric_id,
                environment_id=request.environment_id
            )
            if not source_metric:
                raise CortexNotFoundError(
                    f"Source metric with ID {source_metric_id} not found in environment {request.environment_id}"
                )

            # Construct in-memory variant (same pattern as create_variant but without saving)
            variant = SemanticMetricVariant(
                name=inline.name,
                alias=inline.alias,
                description=inline.description,
                environment_id=request.environment_id,
                data_model_id=source_metric.data_model_id,
                data_source_id=source_metric.data_source_id,
                source_id=source_metric_id,
                source=inline.source,
                overrides=inline.overrides,
                include=inline.include,
                derivations=inline.derivations,
                combine=inline.combine,
                public=inline.public,
                cache=inline.cache,
                refresh=inline.refresh,
                parameters=inline.parameters,
                meta=inline.meta,
            )

            # Execute using the in-memory variant object directly
            result = execution_service.execute_metric(
                metric=variant,
                context_id=request.context_id,
                parameters=request.parameters,
                limit=request.limit,
                offset=request.offset,
                grouped=request.grouped,
                cache_preference=request.cache,
                preview=request.preview,
            )

        # Build error list from result
        errors = None
        if not result["success"]:
            errors = []
            if result.get("error"):
                errors.append(result.get("error"))
            if result.get("validation_errors"):
                errors.extend(result.get("validation_errors", []))

        return MetricVariantExecutionResponse(
            success=result["success"],
            data=result.get("data"),
            metadata=result.get("metadata", {}),
            errors=errors
        )

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()


def override_source(variant_id: UUID) -> Dict[str, Any]:
    """
    Override the source metric with the resolved state of this variant - direct Core service call.

    Args:
        variant_id: Variant ID

    Returns:
        Override result dictionary
    """
    variant_service = MetricVariantService()
    metric_service = MetricService()

    try:
        # Get existing variant
        db_variant = variant_service.get_variant_by_id(variant_id)
        if not db_variant:
            raise CortexNotFoundError(f"Variant with ID {variant_id} not found")

        # Deserialize as variant
        variant = SemanticMetricVariant.model_validate(db_variant, from_attributes=True)

        # Get source ID
        if variant.source.metric_id is None:
            raise ValueError("Cannot override source for variant with inline source metric")

        source_id = variant.source.metric_id

        # Create fetcher for compiler
        def fetcher(mid: UUID):
            # Try to get from variant service first
            db_v = variant_service.get_variant_by_id(mid)
            if db_v:
                return SemanticMetricVariant.model_validate(db_v, from_attributes=True)
            # Otherwise get from metric service
            db_m = metric_service.get_metric_by_id(mid)
            if not db_m:
                raise ValueError(f"Metric with ID {mid} not found")
            return SemanticMetric.model_validate(db_m, from_attributes=True)

        # Compile variant to resolved metric
        resolved_metric = compile_metric(variant, fetcher)

        # Update source metric with resolved state
        updates = {
            "measures": resolved_metric.measures,
            "dimensions": resolved_metric.dimensions,
            "filters": resolved_metric.filters,
            "joins": resolved_metric.joins,
            "order": resolved_metric.order,
            "derivations": resolved_metric.derivations,
            "composition": resolved_metric.composition,
            "table_name": resolved_metric.table_name,
            "limit": resolved_metric.limit,
            "grouped": resolved_metric.grouped,
            "ordered": resolved_metric.ordered,
        }

        updated_source = metric_service.update_metric(source_id, updates)

        return {
            "success": True,
            "data": updated_source,
            "message": "Source metric overridden successfully",
        }

    except Exception as e:
        raise CoreExceptionMapper().map(e)
    finally:
        variant_service.close()
        metric_service.close()
