"""
Request schemas for doctor diagnose endpoints.
"""

from typing import Optional
from uuid import UUID

from pydantic import Field, model_validator

from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.types.telescope import TSModel


class MetricDiagnoseRequest(TSModel):
    """Request to diagnose a metric (by ID or inline definition)."""

    metric_id: Optional[UUID] = Field(
        None, description="ID of a saved metric to diagnose"
    )
    metric: Optional[SemanticMetric] = Field(
        None, description="Inline metric definition to diagnose"
    )
    environment_id: UUID = Field(..., description="Environment ID")

    @model_validator(mode="after")
    def validate_exactly_one(self):
        if self.metric_id is not None and self.metric is not None:
            raise ValueError(
                "Cannot provide both metric_id and metric; provide exactly one"
            )
        if self.metric_id is None and self.metric is None:
            raise ValueError("Must provide either metric_id or metric")
        return self


class VariantDiagnoseRequest(TSModel):
    """Request to diagnose a metric variant (by ID or inline definition)."""

    variant_id: Optional[UUID] = Field(
        None, description="ID of a saved variant to diagnose"
    )
    variant: Optional[SemanticMetricVariant] = Field(
        None, description="Inline variant definition to diagnose"
    )
    environment_id: UUID = Field(..., description="Environment ID")

    @model_validator(mode="after")
    def validate_exactly_one(self):
        if self.variant_id is not None and self.variant is not None:
            raise ValueError(
                "Cannot provide both variant_id and variant; provide exactly one"
            )
        if self.variant_id is None and self.variant is None:
            raise ValueError("Must provide either variant_id or variant")
        return self
