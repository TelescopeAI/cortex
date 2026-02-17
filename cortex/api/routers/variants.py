"""
API router for metric variants.

This module provides REST endpoints for creating, reading, updating, and deleting
metric variants, as well as lifecycle operations (reset, detach, override-source).
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.data.db.metric_service import MetricService
from cortex.core.compiler import compile as compile_metric


# Create router instance
VariantsRouter = APIRouter()


@VariantsRouter.post(
    "/metrics/variants",
    status_code=status.HTTP_201_CREATED,
    tags=["Metric Variants"],
)
async def create_variant(variant_data: dict):
    """
    Create a new metric variant.

    Variants inherit from a source metric and can modify it through overrides,
    inclusions, exclusions, derivations, and multi-source composition.
    """
    try:
        metric_service = MetricService()

        try:
            # Deserialize variant data
            variant = SemanticMetricVariant.model_validate(variant_data)

            # Set metric_type discriminator
            variant_dict = variant.model_dump()
            variant_dict["metric_type"] = "variant"

            # Create variant in database
            db_variant = metric_service.create_metric(variant_dict)

            # Return the created variant
            return {"success": True, "data": db_variant, "message": "Variant created successfully"}

        finally:
            metric_service.close()

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
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def list_variants(
    environment_id: UUID,
    data_model_id: Optional[UUID] = None,
    source_metric_id: Optional[UUID] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
):
    """
    List metric variants with optional filtering.

    Returns only metrics with metric_type = 'variant'.
    Can filter by source_metric_id to get all variants of a specific metric.
    """
    try:
        metric_service = MetricService()

        try:
            # Get all metrics and filter for variants
            all_metrics = metric_service.get_all_metrics(
                environment_id=environment_id,
                data_model_id=data_model_id,
                skip=offset,
                limit=limit,
            )

            # Filter for variants only
            variants = [
                m
                for m in all_metrics
                if hasattr(m, "metric_type") and m.metric_type == "variant"
            ]

            # Additional filter by source_metric_id if provided
            if source_metric_id:
                variants = [
                    v for v in variants
                    if hasattr(v, "source") and v.source and v.source.get("metric_id") == str(source_metric_id)
                ]

            return {
                "success": True,
                "data": variants,
                "total": len(variants),
                "limit": limit,
                "offset": offset,
            }

        finally:
            metric_service.close()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list variants: {str(e)}",
        )


@VariantsRouter.get(
    "/metrics/variants/{variant_id}",
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def get_variant(variant_id: UUID):
    """
    Get a metric variant by ID.

    Returns the variant definition (not the resolved metric).
    """
    try:
        metric_service = MetricService()

        try:
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            return {"success": True, "data": db_variant}

        finally:
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
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants"],
)
async def update_variant(variant_id: UUID, variant_data: dict):
    """
    Update a metric variant.

    Can modify overrides, inclusions, derivations, and combine settings.
    """
    try:
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Build updates dictionary
            updates = {}
            for key, value in variant_data.items():
                if key not in ["id", "created_at", "metric_type"]:
                    updates[key] = value

            # Update variant in database
            updated_variant = metric_service.update_metric(variant_id, updates)

            return {
                "success": True,
                "data": updated_variant,
                "message": "Variant updated successfully",
            }

        finally:
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
async def delete_variant(variant_id: UUID):
    """
    Delete a metric variant.

    This does not affect the source metric.
    """
    try:
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Delete variant
            metric_service.delete_metric(variant_id)

            return None  # 204 No Content

        finally:
            metric_service.close()

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
    tags=["Metric Variants", "Lifecycle"],
)
async def reset_variant(variant_id: UUID):
    """
    Reset a variant by removing all overrides.

    The variant will then exactly match its source metric.
    """
    try:
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Reset overrides
            updates = {
                "overrides": None,
                "include": None,
                "derivations": None,
                "combine": None,
            }

            updated_variant = metric_service.update_metric(variant_id, updates)

            return {
                "success": True,
                "data": updated_variant,
                "message": "Variant reset successfully",
            }

        finally:
            metric_service.close()

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
    tags=["Metric Variants", "Lifecycle"],
)
async def detach_variant(variant_id: UUID):
    """
    Detach a variant by creating a new standalone metric from the resolved state.

    Returns the new metric ID.
    """
    try:
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Deserialize as variant
            variant = SemanticMetricVariant.model_validate(db_variant)

            # Create fetcher for compiler
            def fetcher(mid: UUID):
                db_m = metric_service.get_metric_by_id(mid)
                if not db_m:
                    raise ValueError(f"Metric with ID {mid} not found")
                if hasattr(db_m, "metric_type") and db_m.metric_type == "variant":
                    return SemanticMetricVariant.model_validate(db_m)
                else:
                    return SemanticMetric.model_validate(db_m)

            # Compile variant to resolved metric
            resolved_metric = compile_metric(variant, fetcher)

            # Create new standalone metric
            new_metric_dict = resolved_metric.model_dump()
            new_metric_dict["metric_type"] = "base"
            new_metric_dict["name"] = f"{resolved_metric.name}_detached"
            new_metric_dict.pop("id")  # Let DB generate new ID

            new_metric = metric_service.create_metric(new_metric_dict)

            return {
                "success": True,
                "data": new_metric,
                "message": f"Variant detached as new metric: {new_metric.id}",
            }

        finally:
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
    status_code=status.HTTP_200_OK,
    tags=["Metric Variants", "Execution"],
)
async def execute_variant(variant_id: UUID, execution_request: dict):
    """
    Execute a metric variant and return results.

    The variant is compiled to a resolved metric and then executed.
    """
    try:
        from cortex.core.services.metrics.execution import MetricExecutionService

        metric_service = MetricService()
        execution_service = MetricExecutionService()

        try:
            # Get the variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Execute the variant (execution service handles compilation)
            result = await execution_service.execute_metric(
                metric_id=str(variant_id),
                execution_request=execution_request,
            )

            return result

        finally:
            metric_service.close()

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
    tags=["Metric Variants", "Lifecycle"],
)
async def override_source(variant_id: UUID):
    """
    Override the source metric with the resolved state of this variant.

    WARNING: This modifies the source metric and cannot be undone!
    """
    try:
        metric_service = MetricService()

        try:
            # Get existing variant
            db_variant = metric_service.get_metric_by_id(variant_id)
            if not db_variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Variant with ID {variant_id} not found",
                )

            # Check that it's actually a variant
            if not hasattr(db_variant, "metric_type") or db_variant.metric_type != "variant":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Metric {variant_id} is not a variant",
                )

            # Deserialize as variant
            variant = SemanticMetricVariant.model_validate(db_variant)

            # Get source ID
            if variant.source.metric_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot override source for variant with inline source metric",
                )

            source_id = variant.source.metric_id

            # Create fetcher for compiler
            def fetcher(mid: UUID):
                db_m = metric_service.get_metric_by_id(mid)
                if not db_m:
                    raise ValueError(f"Metric with ID {mid} not found")
                if hasattr(db_m, "metric_type") and db_m.metric_type == "variant":
                    return SemanticMetricVariant.model_validate(db_m)
                else:
                    return SemanticMetric.model_validate(db_m)

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
            metric_service.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to override source: {str(e)}",
        )
