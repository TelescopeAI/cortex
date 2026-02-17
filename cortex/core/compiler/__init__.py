"""
Compiler module for composable metrics system.

This module provides the compile() function that resolves SemanticMetricVariants
into fully-resolved SemanticMetrics. The compiler handles:
- Source chain resolution (variants can inherit from variants)
- Component overrides (add/replace/exclude/include operations)
- Derivation validation
- Multi-source composition via CTEs
"""

from typing import Union
from uuid import UUID

from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.compiler.protocols import MetricFetcher
from cortex.core.compiler.resolver import VariantResolver
from cortex.core.compiler.derivations import DerivationValidator


def compile(
    metric: Union[SemanticMetric, SemanticMetricVariant],
    fetcher: MetricFetcher,
) -> SemanticMetric:
    """
    Compile a metric or variant into a fully-resolved SemanticMetric.

    Args:
        metric: Either a base SemanticMetric or a SemanticMetricVariant to resolve
        fetcher: Protocol for fetching metrics by ID (decouples from DB layer)

    Returns:
        Fully-resolved SemanticMetric ready for query execution

    Process:
        - SemanticMetric: validate derivations if present, return as-is.
        - SemanticMetricVariant: resolve source chain, apply overrides,
          validate derivations, resolve combine into composition, return resolved metric.

    Raises:
        CompilerError: Base exception for all compiler errors
        CircularReferenceError: When variant source chain contains a cycle
        MaxDepthExceededError: When source chain depth exceeds MAX_DEPTH (10)
        InvalidDerivationError: When derivation references invalid measure
        MeasureNotFoundError: When derivation source measure doesn't exist
        IncompatibleSourceError: When combine metric has incompatible dimensions
        InvalidJoinDimensionError: When join_on dimension doesn't exist
    """
    if isinstance(metric, SemanticMetric):
        # Validate derivations if present
        if metric.derivations:
            DerivationValidator.validate(
                metric.derivations, metric.measures, metric.composition
            )
        return metric

    # Variant resolution
    resolver = VariantResolver(fetcher=fetcher)
    resolved = resolver.resolve(metric)

    # Validate derivations in the resolved metric
    if resolved.derivations:
        DerivationValidator.validate(
            resolved.derivations, resolved.measures, resolved.composition
        )

    return resolved


__all__ = [
    "compile",
    "MetricFetcher",
]
