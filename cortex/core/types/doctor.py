"""
Doctor module types for diagnostic results.

These types are used by the doctor module to return structured
diagnosis information about metrics, variants, and other entities.
"""

from typing import List, Optional, Union

from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.types.telescope import TSModel


class Suggestion(TSModel):
    """
    A concrete fix suggestion for an identified issue.

    Each suggestion includes a description of why the error occurred
    and a corrected entity JSON that resolves the issue.
    """

    description: str
    # Put SemanticMetricVariant FIRST - Pydantic v2 smart mode will use runtime type
    # SemanticMetricVariant has unique required field 'source' for better matching
    fixed: Union[SemanticMetricVariant, SemanticMetric]


class Diagnosis(TSModel):
    """
    Full diagnosis result containing an explanation and fix suggestions.

    The explanation covers ALL detected issues (both fixable and non-fixable).
    Suggestions only contain issues where a concrete fix could be generated.
    """

    explanation: str
    suggestions: List[Suggestion]


class DiagnosisResult(TSModel):
    """
    Top-level result returned by the doctor.

    When healthy is True, diagnosis is None (no issues found).
    When healthy is False, diagnosis contains the full analysis.
    """

    healthy: bool
    diagnosis: Optional[Diagnosis] = None
