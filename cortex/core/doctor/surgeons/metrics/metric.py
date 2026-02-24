"""
Metric surgeon — diagnoses issues with SemanticMetric definitions.

Runs through validation stages and collects errors with fix suggestions.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from cortex.core.compiler.derivations import DerivationValidator
from cortex.core.compiler.exceptions import InvalidDerivationError, MeasureNotFoundError
from cortex.core.data.modelling.model import DataModel
from cortex.core.data.modelling.validation_service import ValidationService
from cortex.core.doctor.surgeons.metrics.joins import JoinInferenceService
from cortex.core.query.executor import QueryExecutor
from cortex.core.semantics.joins import JoinCondition, JoinType, SemanticJoin
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.services.data.sources.schemas import DataSourceSchemaService
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.doctor import Diagnosis, DiagnosisResult, Suggestion
from cortex.core.types.sql_schema import DatabaseSchema

logger = logging.getLogger(__name__)


class MetricSurgeon:
    """
    Diagnoses a resolved SemanticMetric by running it through multiple
    validation stages, collecting errors, and generating fix suggestions.
    """

    @staticmethod
    def diagnose(
        metric: SemanticMetric,
        data_model: DataModel,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
    ) -> DiagnosisResult:
        """
        Run all diagnostic stages and return the result.

        Stages:
        1. Structural validation (required fields)
        2. Semantic validation (via ValidationService)
        3. Derivation validation
        4. Missing joins detection + auto-fix
        5. Query generation + execution
        """
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        # Stage 1: Structural validation
        stage1_errors, stage1_suggestions = MetricSurgeon._check_structure(metric)
        errors.extend(stage1_errors)
        suggestions.extend(stage1_suggestions)

        # Stage 2: Semantic validation
        stage2_errors, stage2_suggestions = MetricSurgeon._check_semantics(
            metric, data_model
        )
        errors.extend(stage2_errors)
        suggestions.extend(stage2_suggestions)

        # Stage 3: Derivation validation
        stage3_errors, stage3_suggestions = MetricSurgeon._check_derivations(metric)
        errors.extend(stage3_errors)
        suggestions.extend(stage3_suggestions)

        # Stage 4: Missing joins detection
        stage4_errors, stage4_suggestions = MetricSurgeon._check_joins(metric)
        errors.extend(stage4_errors)
        suggestions.extend(stage4_suggestions)

        # Stage 5: Query generation + execution
        stage5_errors = MetricSurgeon._check_execution(
            metric, data_model, source_type
        )
        errors.extend(stage5_errors)

        if not errors:
            return DiagnosisResult(healthy=True)

        explanation = MetricSurgeon._build_explanation(errors)
        return DiagnosisResult(
            healthy=False,
            diagnosis=Diagnosis(explanation=explanation, suggestions=suggestions),
        )

    @staticmethod
    def _check_structure(
        metric: SemanticMetric,
    ) -> Tuple[List[str], List[Suggestion]]:
        """Stage 1: Check required fields and structural validity."""
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        if not metric.name:
            errors.append("Metric name is required.")

        if not metric.table_name and not metric.query:
            error_msg = "Either 'table_name' or 'query' must be specified."
            errors.append(error_msg)

            # Try to fix: if data_source_id exists, look up schema for table name
            if metric.data_source_id:
                suggested_table = MetricSurgeon._suggest_table_name(
                    metric.data_source_id
                )
                if suggested_table:
                    fixed = metric.model_copy(update={"table_name": suggested_table})
                    suggestions.append(
                        Suggestion(
                            description=(
                                f"Missing table_name. The data source contains "
                                f"table '{suggested_table}' which can be used."
                            ),
                            fixed=fixed,
                        )
                    )

        has_components = (
            (metric.measures and len(metric.measures) > 0)
            or (metric.dimensions and len(metric.dimensions) > 0)
            or (metric.aggregations and len(metric.aggregations) > 0)
        )
        if not has_components:
            errors.append(
                "No measures, dimensions, or aggregations defined. "
                "The metric needs at least one component."
            )

        return errors, suggestions

    @staticmethod
    def _check_semantics(
        metric: SemanticMetric,
        data_model: DataModel,
    ) -> Tuple[List[str], List[Suggestion]]:
        """Stage 2: Run semantic validation."""
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        try:
            result = ValidationService.validate_metric_execution(metric, data_model)
            errors.extend(result.errors)

            # Check for fixable data_model_id mismatch
            if metric.data_model_id != data_model.id:
                fixed = metric.model_copy(update={"data_model_id": data_model.id})
                suggestions.append(
                    Suggestion(
                        description=(
                            f"Metric data_model_id ({metric.data_model_id}) does not "
                            f"match the data model ({data_model.id}). Fixed to match."
                        ),
                        fixed=fixed,
                    )
                )
        except Exception as e:
            errors.append(f"Semantic validation error: {e}")

        return errors, suggestions

    @staticmethod
    def _check_derivations(
        metric: SemanticMetric,
    ) -> Tuple[List[str], List[Suggestion]]:
        """Stage 3: Validate derivations if present."""
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        if not metric.derivations:
            return errors, suggestions

        try:
            DerivationValidator.validate(
                metric.derivations, metric.measures, metric.composition
            )
        except MeasureNotFoundError as e:
            errors.append(str(e))

            # Suggest closest matching measure
            closest = MetricSurgeon._find_closest_match(
                e.measure_name, e.available_measures
            )
            if closest:
                new_derivations = []
                for d in metric.derivations or []:
                    if d.source and d.source.measure == e.measure_name:
                        new_source = d.source.model_copy(update={"measure": closest})
                        new_derivations.append(d.model_copy(update={"source": new_source}))
                    else:
                        new_derivations.append(d)
                fixed = metric.model_copy(update={"derivations": new_derivations})
                suggestions.append(
                    Suggestion(
                        description=(
                            f"Derivation '{e.derivation_name}' references measure "
                            f"'{e.measure_name}' which doesn't exist. "
                            f"Did you mean '{closest}'?"
                        ),
                        fixed=fixed,
                    )
                )
        except InvalidDerivationError as e:
            errors.append(str(e))

            # Try to fix missing required params
            suggestion = MetricSurgeon._fix_derivation_error(metric, e)
            if suggestion:
                suggestions.append(suggestion)
        except Exception as e:
            errors.append(f"Derivation validation error: {e}")

        return errors, suggestions

    @staticmethod
    def _check_joins(
        metric: SemanticMetric,
    ) -> Tuple[List[str], List[Suggestion]]:
        """Stage 4: Detect missing joins and suggest auto-generated ones."""
        errors: List[str] = []
        suggestions: List[Suggestion] = []

        missing_tables = JoinInferenceService.find_missing_join_tables(metric)
        if not missing_tables:
            return errors, suggestions

        errors.append(
            f"Missing FROM-clause entries for tables: {', '.join(sorted(missing_tables))}. "
            f"These tables are referenced in measures/dimensions/filters but have no "
            f"join defined to the base table '{metric.table_name}'."
        )

        # Try to infer joins from schema
        inferred_joins = []
        if metric.data_source_id:
            try:
                schema_service = DataSourceSchemaService()
                schema_response = schema_service.get_schema(metric.data_source_id)
                schema_payload = schema_response.get("schema", {})

                # Parse schema into DatabaseSchema model
                schema = DatabaseSchema.model_validate(schema_payload)

                inferred_joins = JoinInferenceService.infer_missing_joins(
                    metric, schema
                )
            except Exception as e:
                logger.warning(f"Failed to infer joins from schema: {e}")

        if inferred_joins:
            merged_joins = list(metric.joins or []) + inferred_joins
            fixed = metric.model_copy(update={"joins": merged_joins})

            join_descriptions = [
                f"{j.left_table}.{j.conditions[0].left_column} = "
                f"{j.right_table}.{j.conditions[0].right_column}"
                for j in inferred_joins
            ]
            suggestions.append(
                Suggestion(
                    description=(
                        f"Missing joins detected for tables: "
                        f"{', '.join(sorted(missing_tables))}. "
                        f"Auto-generated LEFT JOINs: "
                        f"{'; '.join(join_descriptions)}."
                    ),
                    fixed=fixed,
                )
            )
        else:
            # Fallback: generate skeleton joins using FK naming convention
            # ({singularized_table}_id) when schema inference is unavailable
            base_table = metric.table_name
            fallback_joins = []
            for target_table in sorted(missing_tables):
                singular = JoinInferenceService._singularize(target_table)
                fallback_joins.append(
                    SemanticJoin(
                        name=f"{base_table}_{target_table}_join",
                        description=(
                            f"Suggested join from {base_table} to {target_table}"
                        ),
                        join_type=JoinType.LEFT,
                        left_table=base_table,
                        right_table=target_table,
                        conditions=[
                            JoinCondition(
                                left_table=base_table,
                                left_column=f"{singular}_id",
                                right_table=target_table,
                                right_column="id",
                                operator="=",
                            )
                        ],
                    )
                )

            merged_joins = list(metric.joins or []) + fallback_joins
            fixed = metric.model_copy(update={"joins": merged_joins})

            join_descriptions = [
                f"{j.left_table}.{j.conditions[0].left_column} = "
                f"{j.right_table}.{j.conditions[0].right_column}"
                for j in fallback_joins
            ]
            suggestions.append(
                Suggestion(
                    description=(
                        f"Missing joins detected for tables: "
                        f"{', '.join(sorted(missing_tables))}. "
                        f"Suggested LEFT JOINs using naming convention: "
                        f"{'; '.join(join_descriptions)}. "
                        f"Review and adjust the join columns if needed."
                    ),
                    fixed=fixed,
                )
            )

        return errors, suggestions

    @staticmethod
    def _check_execution(
        metric: SemanticMetric,
        data_model: DataModel,
        source_type: DataSourceTypes,
    ) -> List[str]:
        """Stage 5: Try query generation and execution. Non-fixable errors only."""
        errors: List[str] = []

        try:
            executor = QueryExecutor()
            result = executor.execute_metric(
                metric=metric,
                data_model=data_model,
                source_type=source_type,
                preview=True,
            )

            if not result.get("success", True):
                error_msg = result.get("error", "Query generation failed")
                validation_errors = result.get("validation_errors", [])
                if validation_errors:
                    error_msg += f": {'; '.join(validation_errors)}"
                errors.append(f"Query generation error: {error_msg}")
        except Exception as e:
            errors.append(f"Query execution error: {e}")

        return errors

    @staticmethod
    def _build_explanation(errors: List[str]) -> str:
        """Build a human-readable explanation from collected errors."""
        if len(errors) == 1:
            return f"1 issue found: {errors[0]}"

        lines = [f"{len(errors)} issues found:"]
        for i, error in enumerate(errors, 1):
            lines.append(f"  {i}. {error}")
        return "\n".join(lines)

    @staticmethod
    def _suggest_table_name(data_source_id: UUID) -> Optional[str]:
        """Look up the first available table from a data source's schema."""
        try:
            schema_service = DataSourceSchemaService()
            schema_response = schema_service.get_schema(data_source_id)
            schema_payload = schema_response.get("schema", {})
            tables = schema_payload.get("tables", [])
            if tables:
                first = tables[0]
                return first.get("name") if isinstance(first, dict) else first.name
        except Exception as e:
            logger.warning(
                f"Failed to fetch schema for data source {data_source_id}: {e}"
            )
        return None

    @staticmethod
    def _find_closest_match(target: str, candidates: List[str]) -> Optional[str]:
        """Find the closest matching string from candidates."""
        if not candidates:
            return None

        target_lower = target.lower()

        # Exact match (case insensitive)
        for c in candidates:
            if c.lower() == target_lower:
                return c

        # Substring match
        for c in candidates:
            if target_lower in c.lower() or c.lower() in target_lower:
                return c

        # Common prefix match
        best = None
        best_score = 0
        for c in candidates:
            c_lower = c.lower()
            prefix_len = 0
            for a, b in zip(target_lower, c_lower):
                if a == b:
                    prefix_len += 1
                else:
                    break
            if prefix_len > best_score:
                best_score = prefix_len
                best = c

        return best if best_score > 2 else (candidates[0] if candidates else None)

    @staticmethod
    def _fix_derivation_error(
        metric: SemanticMetric,
        error: InvalidDerivationError,
    ) -> Optional[Suggestion]:
        """Try to fix a derivation error by adding missing required params."""
        if "order_dimension" in error.reason and metric.dimensions:
            first_dim = metric.dimensions[0]
            new_derivations = [
                d.model_copy(update={"order_dimension": first_dim.name})
                if d.name == error.derivation_name else d
                for d in metric.derivations or []
            ]
            fixed = metric.model_copy(update={"derivations": new_derivations})
            return Suggestion(
                description=(
                    f"Derivation '{error.derivation_name}' requires an "
                    f"order_dimension. Set to '{first_dim.name}'."
                ),
                fixed=fixed,
            )

        if "partition_by" in error.reason and metric.dimensions:
            first_dim = metric.dimensions[0]
            new_derivations = [
                d.model_copy(update={"partition_by": first_dim.name})
                if d.name == error.derivation_name else d
                for d in metric.derivations or []
            ]
            fixed = metric.model_copy(update={"derivations": new_derivations})
            return Suggestion(
                description=(
                    f"Derivation '{error.derivation_name}' requires a "
                    f"partition_by field. Set to '{first_dim.name}'."
                ),
                fixed=fixed,
            )

        return None
