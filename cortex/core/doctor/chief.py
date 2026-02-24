"""
Chief orchestrator for the doctor module.

Fetches entities by ID or uses inline definitions, then dispatches
to the appropriate surgeon for diagnosis.
"""

import logging
from typing import Optional
from uuid import UUID

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.metric_variant_service import MetricVariantService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.data.modelling.model import DataModel
from cortex.core.doctor.surgeons.metrics.metric import MetricSurgeon
from cortex.core.doctor.surgeons.metrics.variants import VariantSurgeon
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.doctor import DiagnosisResult

logger = logging.getLogger(__name__)


class CortexDoctor:
    """
    Top-level orchestrator that resolves entities and dispatches to surgeons.
    """

    @staticmethod
    def diagnose_metric(
        metric_id: Optional[UUID] = None,
        metric: Optional[SemanticMetric] = None,
        environment_id: Optional[UUID] = None,
    ) -> DiagnosisResult:
        """
        Diagnose a metric by ID or inline definition.

        Args:
            metric_id: ID of a saved metric to diagnose
            metric: Inline metric definition to diagnose
            environment_id: Environment ID for validation

        Returns:
            DiagnosisResult with health status and optional diagnosis

        Raises:
            ValueError: If neither metric_id nor metric provided, or both provided
            ValueError: If metric or data model not found
        """
        if metric_id is not None and metric is not None:
            raise ValueError(
                "Cannot provide both metric_id and metric; provide exactly one"
            )
        if metric_id is None and metric is None:
            raise ValueError("Must provide either metric_id or metric")

        metric_service = MetricService()
        model_service = DataModelService()

        try:
            # Resolve metric
            if metric_id is not None:
                db_metric = metric_service.get_metric_by_id(metric_id)
                if not db_metric:
                    raise ValueError(f"Metric with ID {metric_id} not found")
                resolved_metric = SemanticMetric.model_validate(
                    db_metric, from_attributes=True
                )
            else:
                resolved_metric = metric

            # Fetch data model
            data_model_orm = model_service.get_data_model_by_id(
                resolved_metric.data_model_id
            )
            if not data_model_orm:
                raise ValueError(
                    f"Data model with ID {resolved_metric.data_model_id} not found"
                )
            data_model = DataModel.model_validate(data_model_orm)

            # Infer source type from data source
            source_type = DataSourceTypes.POSTGRESQL
            if resolved_metric.data_source_id:
                try:
                    data_source = DataSourceCRUD.get_data_source(
                        resolved_metric.data_source_id
                    )
                    source_type = DataSourceTypes(data_source.source_type)
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch data source "
                        f"{resolved_metric.data_source_id}: {e}. "
                        f"Using default source_type."
                    )

            return MetricSurgeon.diagnose(resolved_metric, data_model, source_type)

        finally:
            metric_service.close()
            model_service.close()

    @staticmethod
    def diagnose_variant(
        variant_id: Optional[UUID] = None,
        variant: Optional[SemanticMetricVariant] = None,
        environment_id: Optional[UUID] = None,
    ) -> DiagnosisResult:
        """
        Diagnose a variant by ID or inline definition.

        Args:
            variant_id: ID of a saved variant to diagnose
            variant: Inline variant definition to diagnose
            environment_id: Environment ID for validation

        Returns:
            DiagnosisResult with health status and optional diagnosis

        Raises:
            ValueError: If neither variant_id nor variant provided, or both provided
            ValueError: If variant not found
        """
        if variant_id is not None and variant is not None:
            raise ValueError(
                "Cannot provide both variant_id and variant; provide exactly one"
            )
        if variant_id is None and variant is None:
            raise ValueError("Must provide either variant_id or variant")

        variant_service = MetricVariantService()

        try:
            # Resolve variant
            if variant_id is not None:
                db_variant = variant_service.get_variant_by_id(variant_id)
                if not db_variant:
                    raise ValueError(
                        f"Variant with ID {variant_id} not found"
                    )
                resolved_variant = SemanticMetricVariant.model_validate(
                    db_variant, from_attributes=True
                )
            else:
                resolved_variant = variant

            return VariantSurgeon.diagnose(resolved_variant, environment_id)

        finally:
            variant_service.close()
