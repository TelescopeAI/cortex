"""
Variant surgeon — diagnoses issues with SemanticMetricVariant definitions.

Compiles the variant first, catching compiler errors, then delegates
to MetricSurgeon for the resolved metric.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from cortex.core.compiler import compile as compile_metric
from cortex.core.compiler.exceptions import (
    CircularReferenceError,
    CompilerError,
    IncompatibleSourceError,
    InvalidDerivationError,
    InvalidJoinDimensionError,
    MaxDepthExceededError,
    MeasureNotFoundError,
)
from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.metric_variant_service import MetricVariantService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.data.modelling.model import DataModel
from cortex.core.doctor.surgeons.metrics.metric import MetricSurgeon
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.overrides import MetricOverrides, OverrideComponents
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.doctor import Diagnosis, DiagnosisResult, Suggestion

logger = logging.getLogger(__name__)


class VariantSurgeon:
    """
    Diagnoses a SemanticMetricVariant by compiling it and then
    running the resolved metric through MetricSurgeon.
    """

    @staticmethod
    def diagnose(
        variant: SemanticMetricVariant,
        environment_id: UUID,
    ) -> DiagnosisResult:
        """
        Diagnose a variant by compiling it and checking the resolved metric.

        Stage 0: Compilation (variant-specific errors)
        Stages 1-5: Delegated to MetricSurgeon on the resolved metric
        """
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        metric_service = MetricService()
        variant_service = MetricVariantService()

        try:
            # Build fetcher for compiler (same pattern as MetricExecutionService)
            def fetcher(mid: UUID):
                db_v = variant_service.get_variant_by_id(mid)
                if db_v:
                    return SemanticMetricVariant.model_validate(
                        db_v, from_attributes=True
                    )
                db_m = metric_service.get_metric_by_id(mid)
                if not db_m:
                    raise ValueError(f"Metric with ID {mid} not found")
                return SemanticMetric.model_validate(db_m, from_attributes=True)

            # Stage 0: Compilation
            resolved_metric = None
            try:
                resolved_metric = compile_metric(variant, fetcher)
            except CircularReferenceError as e:
                errors.append(f"Circular reference in variant chain: {e}")
            except MaxDepthExceededError as e:
                errors.append(f"Variant chain too deep: {e}")
            except IncompatibleSourceError as e:
                errors.append(str(e))
                suggestion = VariantSurgeon._fix_incompatible_source(
                    variant, e, metric_service
                )
                if suggestion:
                    suggestions.append(suggestion)
            except InvalidJoinDimensionError as e:
                errors.append(str(e))
                suggestion = VariantSurgeon._fix_join_dimension(variant, e)
                if suggestion:
                    suggestions.append(suggestion)
            except MeasureNotFoundError as e:
                errors.append(str(e))
                closest = MetricSurgeon._find_closest_match(
                    e.measure_name, e.available_measures
                )
                if closest:
                    new_derivations = []
                    for d in variant.derivations or []:
                        if d.source and d.source.measure == e.measure_name:
                            new_source = d.source.model_copy(update={"measure": closest})
                            new_derivations.append(d.model_copy(update={"source": new_source}))
                        else:
                            new_derivations.append(d)
                    fixed = variant.model_copy(update={"derivations": new_derivations})
                    suggestions.append(
                        Suggestion(
                            description=(
                                f"Derivation '{e.derivation_name}' references "
                                f"measure '{e.measure_name}' which doesn't exist. "
                                f"Did you mean '{closest}'?"
                            ),
                            fixed=fixed,
                        )
                    )
            except InvalidDerivationError as e:
                errors.append(str(e))
            except CompilerError as e:
                errors.append(f"Compilation error: {e}")
            except Exception as e:
                errors.append(f"Unexpected compilation error: {e}")

            # If compilation succeeded, delegate to MetricSurgeon
            if resolved_metric is not None:
                model_service = DataModelService()
                try:
                    data_model_orm = model_service.get_data_model_by_id(
                        resolved_metric.data_model_id
                    )
                    if not data_model_orm:
                        errors.append(
                            f"Data model with ID {resolved_metric.data_model_id} "
                            f"not found"
                        )
                    else:
                        data_model = DataModel.model_validate(data_model_orm)

                        # Infer source type
                        source_type = DataSourceTypes.POSTGRESQL
                        if resolved_metric.data_source_id:
                            try:
                                data_source = DataSourceCRUD.get_data_source(
                                    resolved_metric.data_source_id
                                )
                                source_type = DataSourceTypes(
                                    data_source.source_type
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Failed to fetch data source: {e}. "
                                    f"Using default source_type."
                                )

                        # Run metric-level diagnosis
                        metric_result = MetricSurgeon.diagnose(
                            resolved_metric, data_model, source_type
                        )

                        if not metric_result.healthy and metric_result.diagnosis:
                            errors.append(metric_result.diagnosis.explanation)
                            translated = VariantSurgeon._translate_metric_suggestions(
                                variant,
                                resolved_metric,
                                metric_result.diagnosis.suggestions,
                            )
                            suggestions.extend(translated)
                finally:
                    model_service.close()

        finally:
            metric_service.close()
            variant_service.close()

        if not errors:
            return DiagnosisResult(healthy=True)

        explanation = VariantSurgeon._build_explanation(errors)
        return DiagnosisResult(
            healthy=False,
            diagnosis=Diagnosis(explanation=explanation, suggestions=suggestions),
        )

    @staticmethod
    def _fix_incompatible_source(
        variant: SemanticMetricVariant,
        error: IncompatibleSourceError,
        metric_service: MetricService,
    ) -> Optional[Suggestion]:
        """Fix mismatched environment/data_model/data_source IDs."""
        if not variant.source or not variant.source.metric_id:
            return None

        try:
            source_metric = metric_service.get_metric_by_id(
                variant.source.metric_id
            )
            if not source_metric:
                return None

            fixed = variant.model_copy(update={
                "environment_id": source_metric.environment_id,
                "data_model_id": source_metric.data_model_id,
                "data_source_id": source_metric.data_source_id,
            })

            return Suggestion(
                description=(
                    f"Variant has incompatible source binding: {error.reason}. "
                    f"Fixed environment_id, data_model_id, and data_source_id "
                    f"to match the source metric."
                ),
                fixed=fixed,
            )
        except Exception as e:
            logger.warning(f"Failed to fix incompatible source: {e}")
            return None

    @staticmethod
    def _fix_join_dimension(
        variant: SemanticMetricVariant,
        error: InvalidJoinDimensionError,
    ) -> Optional[Suggestion]:
        """Suggest closest matching dimension for invalid join_on."""
        all_dims = set(error.primary_dimensions) | set(error.combine_dimensions)
        closest = MetricSurgeon._find_closest_match(
            error.dimension_name, list(all_dims)
        )

        if not closest:
            return None

        new_combine = []
        for ref in variant.combine or []:
            new_join_on = [
                closest if dim == error.dimension_name else dim
                for dim in ref.join_on or []
            ]
            new_combine.append(ref.model_copy(update={"join_on": new_join_on}))
        fixed = variant.model_copy(update={"combine": new_combine})

        return Suggestion(
            description=(
                f"Join dimension '{error.dimension_name}' for combine metric "
                f"'{error.combine_alias}' doesn't exist on both metrics. "
                f"Did you mean '{closest}'?"
            ),
            fixed=fixed,
        )

    @staticmethod
    def _translate_metric_suggestions(
        variant: SemanticMetricVariant,
        resolved_metric: SemanticMetric,
        suggestions: List[Suggestion],
    ) -> List[Suggestion]:
        """
        Translate MetricSurgeon suggestions (metric-shaped fixed) into
        variant-shaped fixed objects by diffing against the resolved metric
        and expressing changes as variant overrides.
        """
        translated = []

        for suggestion in suggestions:
            fixed_metric = suggestion.fixed  # Already a SemanticMetric model instance
            existing_overrides = variant.overrides or MetricOverrides()

            # Diff components (measures, dimensions, filters, joins)
            add_updates: Dict[str, list] = {}
            replace_updates: Dict[str, list] = {}

            for comp_name in ("measures", "dimensions", "filters", "joins"):
                resolved_items = getattr(resolved_metric, comp_name) or []
                fixed_items = getattr(fixed_metric, comp_name) or []
                resolved_by_name = {
                    item.name: item for item in resolved_items
                }

                new_items = [
                    item
                    for item in fixed_items
                    if item.name not in resolved_by_name
                ]
                modified_items = [
                    item
                    for item in fixed_items
                    if item.name in resolved_by_name
                    and item != resolved_by_name[item.name]
                ]

                if new_items:
                    existing_add = (
                        existing_overrides.add or OverrideComponents()
                    )
                    merged = list(
                        getattr(existing_add, comp_name) or []
                    )
                    merged.extend(new_items)
                    add_updates[comp_name] = merged

                if modified_items:
                    replace_updates[comp_name] = modified_items

            # Build overrides update dict
            overrides_update: Dict[str, Any] = {}

            if add_updates:
                base_add = existing_overrides.add or OverrideComponents()
                overrides_update["add"] = base_add.model_copy(
                    update=add_updates
                )

            if replace_updates:
                base_replace = (
                    existing_overrides.replace or OverrideComponents()
                )
                overrides_update["replace"] = base_replace.model_copy(
                    update=replace_updates
                )

            # Scalar field overrides
            for field in ("table_name", "limit", "grouped", "ordered"):
                fixed_val = getattr(fixed_metric, field)
                resolved_val = getattr(resolved_metric, field)
                if fixed_val != resolved_val:
                    overrides_update[field] = fixed_val

            new_overrides = (
                existing_overrides.model_copy(update=overrides_update)
                if overrides_update
                else existing_overrides
            )

            # Build variant update dict
            variant_update: Dict[str, Any] = {"overrides": new_overrides}

            # Binding field overrides
            for field in ("data_model_id", "data_source_id", "environment_id"):
                fixed_val = getattr(fixed_metric, field, None)
                resolved_val = getattr(resolved_metric, field, None)
                if fixed_val and fixed_val != resolved_val:
                    variant_update[field] = fixed_val

            # Derivation changes
            if fixed_metric.derivations != resolved_metric.derivations:
                variant_update["derivations"] = fixed_metric.derivations

            fixed_variant = variant.model_copy(update=variant_update)

            translated.append(
                Suggestion(
                    description=suggestion.description,
                    fixed=fixed_variant,  # Store model instance directly
                )
            )

        return translated

    @staticmethod
    def _build_explanation(errors: List[str]) -> str:
        """Build a human-readable explanation from collected errors."""
        if len(errors) == 1:
            return f"1 issue found: {errors[0]}"

        lines = [f"{len(errors)} issues found:"]
        for i, error in enumerate(errors, 1):
            lines.append(f"  {i}. {error}")
        return "\n".join(lines)
