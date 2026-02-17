"""
Exception classes for the compiler module.

This module defines all exceptions that can be raised during metric compilation,
including variant resolution, derivation validation, and composition errors.
"""

from typing import List, Optional
from uuid import UUID


class CompilerError(Exception):
    """
    Base exception for all compiler errors.

    All exceptions raised by the compiler module inherit from this class,
    making it easy to catch all compiler-related errors.
    """

    pass


class CircularReferenceError(CompilerError):
    """
    Raised when a circular reference is detected in the variant source chain.

    Example: Variant A → Variant B → Variant C → Variant A

    Attributes:
        chain: List of metric IDs forming the circular reference
    """

    def __init__(self, chain: List[UUID], message: Optional[str] = None):
        self.chain = chain
        if message is None:
            chain_str = " → ".join(str(id) for id in chain)
            message = f"Circular reference detected in variant chain: {chain_str}"
        super().__init__(message)


class MaxDepthExceededError(CompilerError):
    """
    Raised when the variant source chain depth exceeds MAX_DEPTH (10).

    This prevents infinite recursion and catches pathologically deep variant chains.

    Attributes:
        depth: The depth at which the error was raised
        max_depth: The maximum allowed depth
    """

    def __init__(self, depth: int, max_depth: int = 10):
        self.depth = depth
        self.max_depth = max_depth
        super().__init__(
            f"Variant source chain depth ({depth}) exceeds maximum allowed depth ({max_depth})"
        )


class InvalidDerivationError(CompilerError):
    """
    Raised when a derivation is invalid.

    This is a general exception for derivation validation errors that don't
    fit into more specific categories.

    Attributes:
        derivation_name: Name of the invalid derivation
        reason: Description of why the derivation is invalid
    """

    def __init__(self, derivation_name: str, reason: str):
        self.derivation_name = derivation_name
        self.reason = reason
        super().__init__(f"Invalid derivation '{derivation_name}': {reason}")


class MeasureNotFoundError(CompilerError):
    """
    Raised when a derivation references a measure that doesn't exist.

    This can occur when:
    - A derivation's source.measure doesn't exist in the resolved measures
    - A derivation's source.by doesn't exist (for two-input operations)
    - A cross-CTE reference (alias.measure) points to a non-existent measure

    Attributes:
        derivation_name: Name of the derivation with the invalid reference
        measure_name: Name of the measure that wasn't found
        available_measures: List of available measure names
    """

    def __init__(
        self,
        derivation_name: str,
        measure_name: str,
        available_measures: List[str],
    ):
        self.derivation_name = derivation_name
        self.measure_name = measure_name
        self.available_measures = available_measures
        super().__init__(
            f"Derivation '{derivation_name}' references measure '{measure_name}' "
            f"which doesn't exist. Available measures: {', '.join(available_measures)}"
        )


class IncompatibleSourceError(CompilerError):
    """
    Raised when a combine source is incompatible with the primary metric.

    This can occur when:
    - The combine metric's data_source_id differs from the primary metric
    - The combine metric's environment_id differs from the primary metric
    - The combine metric has incompatible structure

    Attributes:
        primary_metric_name: Name of the primary metric
        combine_metric_name: Name of the incompatible combine metric
        reason: Description of the incompatibility
    """

    def __init__(
        self, primary_metric_name: str, combine_metric_name: str, reason: str
    ):
        self.primary_metric_name = primary_metric_name
        self.combine_metric_name = combine_metric_name
        self.reason = reason
        super().__init__(
            f"Combine metric '{combine_metric_name}' is incompatible with "
            f"primary metric '{primary_metric_name}': {reason}"
        )


class InvalidJoinDimensionError(CompilerError):
    """
    Raised when a join_on dimension doesn't exist on one or both metrics.

    This occurs during CTE composition when a combine metric specifies join_on
    dimensions that don't exist on the primary metric or the combine metric.

    Attributes:
        combine_alias: Alias of the combine metric
        dimension_name: Name of the invalid join dimension
        primary_dimensions: List of available dimensions on primary metric
        combine_dimensions: List of available dimensions on combine metric
    """

    def __init__(
        self,
        combine_alias: str,
        dimension_name: str,
        primary_dimensions: List[str],
        combine_dimensions: List[str],
    ):
        self.combine_alias = combine_alias
        self.dimension_name = dimension_name
        self.primary_dimensions = primary_dimensions
        self.combine_dimensions = combine_dimensions
        super().__init__(
            f"Join dimension '{dimension_name}' specified for combine metric '{combine_alias}' "
            f"doesn't exist on both metrics. Primary dimensions: {', '.join(primary_dimensions)}. "
            f"Combine dimensions: {', '.join(combine_dimensions)}"
        )


__all__ = [
    "CompilerError",
    "CircularReferenceError",
    "MaxDepthExceededError",
    "InvalidDerivationError",
    "MeasureNotFoundError",
    "IncompatibleSourceError",
    "InvalidJoinDimensionError",
]
