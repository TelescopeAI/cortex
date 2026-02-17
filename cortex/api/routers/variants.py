"""
API router for metric variants.

This module provides REST endpoints for creating, reading, updating, and deleting
metric variants, as well as lifecycle operations (reset, detach, override-source).
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Query

from cortex.api.schemas.requests.variants import (
    MetricVariantCreateRequest,
    MetricVariantUpdateRequest,
    MetricVariantExecutionRequest,
    MetricVariantCloneRequest
)
from cortex.api.schemas.responses.variants import (
    MetricVariantResponse,
    MetricVariantListResponse,
    MetricVariantExecutionResponse
)
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.metric_variant_service import MetricVariantService
from cortex.core.compiler import compile as compile_metric


# Create router instance
VariantsRouter = APIRouter()


@VariantsRouter.post(
    "/metrics/variants",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Metric Variants"],
)
async def create_variant(variant_request: MetricVariantCreateRequest):
    """
    Create a new metric variant.

    Variants inherit from a source metric and can modify it through overrides,
    inclusions, exclusions, derivations, and multi-source composition.
    """
    try:
        variant_service = MetricVariantService()
        metric_service = MetricService()

        try:
            # Verify source metric exists and belongs to the environment
            source_metric_id = variant_request.source.metric_id
            if not source_metric_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Source metric_id is required"
                )

            source_metric = metric_service.get_metric_by_id(
                source_metric_id,
                environment_id=variant_request.environment_id
            )
            if not source_metric:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source metric with ID {source_metric_id} not found in environment {variant_request.environment_id}"
                )

            # Create variant model with explicit environment/data_model/data_source binding and source_id
            variant = SemanticMetricVariant(
                name=variant_request.name,
                alias=variant_request.alias,
                description=variant_request.description,
                environment_id=variant_request.environment_id,
                data_model_id=source_metric.data_model_id,
                data_source_id=source_metric.data_source_id,
                source_id=source_metric_id,  # For CASCADE DELETE when source metric is deleted
                source=variant_request.source,
                overrides=variant_request.overrides,
                include=variant_request.include,
                derivations=variant_request.derivations,
                combine=variant_request.combine,
                public=variant_request.public,
                cache=variant_request.cache,
                refresh=variant_request.refresh,
                parameters=variant_request.parameters,
                meta=variant_request.meta
            )

            # Create via MetricVariantService (NO dict conversion, pass Pydantic directly)
            db_variant = variant_service.create_variant(variant)

            # Convert to response
            response = MetricVariantResponse.model_validate(db_variant)

            # Add source metric name
            response.source_metric_name = source_metric.name

            return response

        finally:
            variant_service.close()
            metric_service.close()

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create variant: {str(e)}",
        )


@VariantsRouter.get(
    "/metrics/variants",
    response_model=MetricVariantListResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def list_variants(
    environment_id: UUID = Query(..., description="Environment ID"),
    data_model_id: Optional[UUID] = Query(None, description="Filter by data model ID"),
    source_metric_id: Optional[UUID] = Query(None, description="Filter by source metric ID"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
):
    """
    List metric variants with optional filtering.

    Can filter by source_metric_id to get all variants of a specific metric.
    """
    try:
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

        finally:
            variant_service.close()
            metric_service.close()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list variants: {str(e)}",
        )


@VariantsRouter.get(
    "/metrics/variants/{variant_id}",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def get_variant(
    variant_id: UUID,
    environment_id: UUID = Query(..., description="Environment ID")
):
    """
    Get a metric variant by ID.

    Returns the variant definition (not the resolved metric).
    """
    try:
        variant_service = MetricVariantService()
        metric_service = MetricService()

        try:
            db_variant = variant_service.get_variant_by_id(variant_id, environment_id=environment_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found in environment {environment_id}",
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

        finally:
            variant_service.close()
            metric_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get variant: {str(e)}",
        )


@VariantsRouter.put(
    "/metrics/variants/{variant_id}",
    response_model=MetricVariantResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def update_variant(variant_id: UUID, variant_request: MetricVariantUpdateRequest):
    """
    Update a metric variant.

    Can modify overrides, inclusions, derivations, and combine settings.
    """
    try:
        variant_service = MetricVariantService()
        metric_service = MetricService()

        try:
            # Get existing variant and validate environment
            db_variant = variant_service.get_variant_by_id(variant_id, environment_id=variant_request.environment_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found in environment {variant_request.environment_id}",
                )

            # Build updates dictionary directly from request fields (only non-None values)
            updates = {}
            if variant_request.name is not None:
                updates["name"] = variant_request.name
            if variant_request.alias is not None:
                updates["alias"] = variant_request.alias
            if variant_request.description is not None:
                updates["description"] = variant_request.description
            if variant_request.source is not None:
                updates["source"] = variant_request.source.model_dump() if hasattr(variant_request.source, 'model_dump') else variant_request.source
            if variant_request.overrides is not None:
                updates["overrides"] = variant_request.overrides.model_dump() if hasattr(variant_request.overrides, 'model_dump') else variant_request.overrides
            if variant_request.include is not None:
                updates["include"] = variant_request.include.model_dump() if hasattr(variant_request.include, 'model_dump') else variant_request.include
            if variant_request.derivations is not None:
                updates["derivations"] = [d.model_dump() for d in variant_request.derivations] if variant_request.derivations else None
            if variant_request.combine is not None:
                updates["combine"] = [c.model_dump() for c in variant_request.combine] if variant_request.combine else None
            if variant_request.public is not None:
                updates["public"] = variant_request.public
            if variant_request.cache is not None:
                updates["cache"] = variant_request.cache.model_dump() if hasattr(variant_request.cache, 'model_dump') else variant_request.cache
            if variant_request.refresh is not None:
                updates["refresh"] = variant_request.refresh.model_dump() if hasattr(variant_request.refresh, 'model_dump') else variant_request.refresh
            if variant_request.parameters is not None:
                updates["parameters"] = {k: v.model_dump() for k, v in variant_request.parameters.items()} if variant_request.parameters else None
            if variant_request.meta is not None:
                updates["meta"] = variant_request.meta

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

        finally:
            variant_service.close()
            metric_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update variant: {str(e)}",
        )


@VariantsRouter.delete(
    "/metrics/variants/{variant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Metric Variants"],
)
async def delete_variant(
    variant_id: UUID,
    environment_id: UUID = Query(..., description="Environment ID")
):
    """
    Delete a metric variant.

    This does not affect the source metric. All variant versions are also deleted (CASCADE).
    """
    try:
        variant_service = MetricVariantService()

        try:
            # Get existing variant and validate environment
            db_variant = variant_service.get_variant_by_id(variant_id, environment_id=environment_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found in environment {environment_id}",
                )

            # Delete variant (cascades to versions)
            variant_service.delete_variant(variant_id)

            return None  # 204 No Content

        finally:
            variant_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete variant: {str(e)}",
        )


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/reset",
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def reset_variant(variant_id: UUID):
    """
    Reset a variant by removing all overrides.

    The variant will then exactly match its source metric.
    """
    try:
        variant_service = MetricVariantService()

        try:
            # Get existing variant
            db_variant = variant_service.get_variant_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

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

        finally:
            variant_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset variant: {str(e)}",
        )


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/detach",
    status_code=status.HTTP_201_CREATED,
    tags=["Metric Variants"],
)
async def detach_variant(variant_id: UUID):
    """
    Detach a variant by creating a new standalone metric from the resolved state.

    Returns the new metric ID.
    """
    try:
        variant_service = MetricVariantService()
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = variant_service.get_variant_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

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
            new_metric_dict.pop("id")  # Let DB generate new ID

            new_metric = metric_service.create_metric(new_metric_dict)

            return {
                "success": True,
                "data": new_metric,
                "message": f"Variant detached as new metric: {new_metric.id}",
            }

        finally:
            variant_service.close()
            metric_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detach variant: {str(e)}",
        )


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/execute",
    response_model=MetricVariantExecutionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants", "Execution"],
)
async def execute_variant(variant_id: UUID, execution_request: MetricVariantExecutionRequest):
    """
    Execute a metric variant and return results.

    The variant is compiled to a resolved metric and then executed.
    """
    try:
        from cortex.core.services.metrics.execution import MetricExecutionService

        variant_service = MetricVariantService()
        execution_service = MetricExecutionService()

        try:
            # Get the variant and validate environment
            db_variant = variant_service.get_variant_by_id(variant_id, environment_id=execution_request.environment_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found in environment {execution_request.environment_id}",
                )

            # Execute the variant (execution service handles compilation)
            result = execution_service.execute_metric(
                metric_id=str(variant_id),
                context_id=execution_request.context_id,
                parameters=execution_request.parameters,
                limit=execution_request.limit,
                offset=execution_request.offset,
                grouped=execution_request.grouped,
                cache_preference=execution_request.cache,
                preview=execution_request.preview,
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

        finally:
            variant_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute variant: {str(e)}",
        )


@VariantsRouter.post(
    "/metrics/variants/{variant_id}/override-source",
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def override_source(variant_id: UUID):
    """
    Override the source metric with the resolved state of this variant.

    WARNING: This modifies the source metric and cannot be undone!
    """
    try:
        variant_service = MetricVariantService()
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = variant_service.get_variant_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Deserialize as variant
            variant = SemanticMetricVariant.model_validate(db_variant, from_attributes=True)

            # Get source ID
            if variant.source.metric_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot override source for variant with inline source metric",
                )

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

        finally:
            variant_service.close()
            metric_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to override source: {str(e)}",
        )
