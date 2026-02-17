"""
Derivation validator for composable metrics system.

This module implements the DerivationValidator class which validates that:
- All derivation source measure references exist in the resolved measures list
- Cross-CTE references (alias.measure) point to valid measures in composition
- Type-specific required fields are present (order_dimension, n, offset, etc.)
"""

from typing import List, Optional, Dict

from cortex.core.semantics.derivations import DerivedEntity, DerivedEntityType
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.compiler.exceptions import (
    InvalidDerivationError,
    MeasureNotFoundError,
)


class DerivationValidator:
    """
    Validates derivations in resolved metrics.

    Checks that all measure references in derivations point to valid measures
    and that type-specific required fields are present.
    """

    # Derivation types that require order_dimension
    REQUIRES_ORDER_DIMENSION = {
        DerivedEntityType.RUNNING_TOTAL,
        DerivedEntityType.CUMULATIVE_COUNT,
        DerivedEntityType.ROW_NUMBER,
        DerivedEntityType.RANK,
        DerivedEntityType.DENSE_RANK,
        DerivedEntityType.PERCENT_RANK,
        DerivedEntityType.CUME_DIST,
        DerivedEntityType.NTILE,
        DerivedEntityType.LAG,
        DerivedEntityType.LEAD,
        DerivedEntityType.FIRST_VALUE,
        DerivedEntityType.LAST_VALUE,
        DerivedEntityType.NTH_VALUE,
    }

    # Derivation types that require partition_by
    REQUIRES_PARTITION_BY = {
        DerivedEntityType.SHARE,
    }

    # Derivation types that require n parameter
    REQUIRES_N = {
        DerivedEntityType.NTILE,
        DerivedEntityType.NTH_VALUE,
    }

    # Two-input arithmetic operations that require source.by
    REQUIRES_BY = {
        DerivedEntityType.DIVIDE,
        DerivedEntityType.MULTIPLY,
        DerivedEntityType.SUBTRACT,
        DerivedEntityType.ADD,
    }

    @classmethod
    def validate(
        cls,
        derivations: List[DerivedEntity],
        measures: Optional[List[SemanticMeasure]],
        composition: Optional[List] = None,  # List[CompositionSource]
    ) -> None:
        """
        Validate all derivations in a metric.

        Args:
            derivations: List of derived entities to validate
            measures: List of measures available in the metric
            composition: Optional list of CompositionSource for cross-CTE validation

        Raises:
            InvalidDerivationError: If a derivation is invalid
            MeasureNotFoundError: If a derivation references a non-existent measure
        """
        # Build a set of available measure names for quick lookup
        available_measures = set()
        if measures is not None:
            available_measures = {m.name for m in measures}

        # Build a map of composition measures (alias -> measure names)
        composition_measures: Dict[str, set] = {}
        if composition is not None:
            for comp_source in composition:
                alias = comp_source.alias
                if comp_source.metric.measures is not None:
                    composition_measures[alias] = {
                        m.name for m in comp_source.metric.measures
                    }

        # Validate each derivation
        for derivation in derivations:
            cls._validate_derivation(
                derivation, available_measures, composition_measures
            )

    @classmethod
    def _validate_derivation(
        cls,
        derivation: DerivedEntity,
        available_measures: set,
        composition_measures: Dict[str, set],
    ) -> None:
        """
        Validate a single derivation.

        Args:
            derivation: The derivation to validate
            available_measures: Set of available measure names on the primary metric
            composition_measures: Dict mapping CTE alias to set of measure names

        Raises:
            InvalidDerivationError: If the derivation is invalid
            MeasureNotFoundError: If a measure reference doesn't exist
        """
        # Validate source measure reference
        cls._validate_measure_reference(
            derivation.name,
            derivation.source.measure,
            available_measures,
            composition_measures,
        )

        # Validate source.by for two-input operations
        if derivation.type in cls.REQUIRES_BY:
            if derivation.source.by is None:
                raise InvalidDerivationError(
                    derivation.name,
                    f"Derivation type '{derivation.type}' requires source.by parameter",
                )
            cls._validate_measure_reference(
                derivation.name,
                derivation.source.by,
                available_measures,
                composition_measures,
            )

        # Validate type-specific required fields
        if derivation.type in cls.REQUIRES_ORDER_DIMENSION:
            if derivation.order_dimension is None:
                raise InvalidDerivationError(
                    derivation.name,
                    f"Derivation type '{derivation.type}' requires order_dimension parameter",
                )

        if derivation.type in cls.REQUIRES_PARTITION_BY:
            if derivation.partition_by is None:
                raise InvalidDerivationError(
                    derivation.name,
                    f"Derivation type '{derivation.type}' requires partition_by parameter",
                )

        if derivation.type in cls.REQUIRES_N:
            if derivation.n is None:
                raise InvalidDerivationError(
                    derivation.name,
                    f"Derivation type '{derivation.type}' requires n parameter",
                )

    @classmethod
    def _validate_measure_reference(
        cls,
        derivation_name: str,
        measure_ref: str,
        available_measures: set,
        composition_measures: Dict[str, set],
    ) -> None:
        """
        Validate that a measure reference exists.

        Handles both local references (measure_name) and cross-CTE references (alias.measure_name).

        Args:
            derivation_name: Name of the derivation for error messages
            measure_ref: The measure reference to validate (e.g., "total_revenue" or "sales.total_revenue")
            available_measures: Set of available measure names on the primary metric
            composition_measures: Dict mapping CTE alias to set of measure names

        Raises:
            MeasureNotFoundError: If the measure reference doesn't exist
        """
        # Check if this is a cross-CTE reference (alias.measure)
        if "." in measure_ref:
            parts = measure_ref.split(".", 1)
            if len(parts) != 2:
                raise InvalidDerivationError(
                    derivation_name,
                    f"Invalid cross-CTE measure reference '{measure_ref}' - expected format: alias.measure",
                )

            alias, measure_name = parts

            # Check if alias exists in composition
            if alias not in composition_measures:
                raise InvalidDerivationError(
                    derivation_name,
                    f"Cross-CTE reference '{measure_ref}' references unknown alias '{alias}'",
                )

            # Check if measure exists on that CTE
            if measure_name not in composition_measures[alias]:
                raise MeasureNotFoundError(
                    derivation_name,
                    measure_ref,
                    list(composition_measures[alias]),
                )
        else:
            # Local reference - check primary measures
            if measure_ref not in available_measures:
                raise MeasureNotFoundError(
                    derivation_name,
                    measure_ref,
                    list(available_measures),
                )
