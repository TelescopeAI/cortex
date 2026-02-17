"""
CTE composer for composable metrics system.

This module handles multi-source composition (combine) for metrics,
building CompositionSource objects for CTE-based query generation.
"""

from typing import List
from uuid import UUID

from cortex.core.semantics.metrics.metric import SemanticMetric, CompositionSource, MetricRef
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.compiler.protocols import MetricFetcher
from cortex.core.compiler.exceptions import (
    InvalidJoinDimensionError,
    IncompatibleSourceError,
)


class CTEComposer:
    """
    Handles multi-source composition for CTE-based queries.

    Resolves combine references and builds CompositionSource objects
    that are stored on the resolved metric for query generation.
    """

    def __init__(self, fetcher: MetricFetcher):
        """
        Initialize the composer with a metric fetcher.

        Args:
            fetcher: Protocol for fetching metrics by ID
        """
        self.fetcher = fetcher

    def compose(
        self,
        primary_metric: SemanticMetric,
        combine_refs: List[MetricRef],
    ) -> List[CompositionSource]:
        """
        Resolve combine references into CompositionSource objects.

        Args:
            primary_metric: The primary/base metric
            combine_refs: List of MetricRef objects to combine

        Returns:
            List of CompositionSource objects ready for CTE generation

        Raises:
            InvalidJoinDimensionError: If join_on dimensions don't exist
            IncompatibleSourceError: If combine metric is incompatible
        """
        composition = []

        for ref in combine_refs:
            # Fetch and resolve the combine metric
            combine_metric = self._fetch_and_resolve(ref)

            # Validate compatibility
            self._validate_compatibility(primary_metric, combine_metric)

            # Get alias (from ref or metric)
            alias = ref.alias or combine_metric.alias or combine_metric.name

            # Get join_on dimensions
            join_on = ref.join_on or []
            if not join_on:
                raise InvalidJoinDimensionError(
                    alias,
                    "(none specified)",
                    self._get_dimension_names(primary_metric),
                    self._get_dimension_names(combine_metric),
                )

            # Validate that join_on dimensions exist on both metrics
            primary_dims = set(self._get_dimension_names(primary_metric))
            combine_dims = set(self._get_dimension_names(combine_metric))

            for dim_name in join_on:
                if dim_name not in primary_dims:
                    raise InvalidJoinDimensionError(
                        alias,
                        dim_name,
                        list(primary_dims),
                        list(combine_dims),
                    )
                if dim_name not in combine_dims:
                    raise InvalidJoinDimensionError(
                        alias,
                        dim_name,
                        list(primary_dims),
                        list(combine_dims),
                    )

            # Build CompositionSource
            comp_source = CompositionSource(
                alias=alias,
                metric=combine_metric,
                join_on=join_on,
            )
            composition.append(comp_source)

        return composition

    def _fetch_and_resolve(self, ref: MetricRef) -> SemanticMetric:
        """
        Fetch and resolve a metric reference.

        Args:
            ref: MetricRef to resolve

        Returns:
            Resolved SemanticMetric
        """
        if ref.metric is not None:
            # Inline metric - use as-is if SemanticMetric, compile if variant
            if isinstance(ref.metric, SemanticMetricVariant):
                # Import here to avoid circular dependency
                from cortex.core.compiler.resolver import VariantResolver

                resolver = VariantResolver(fetcher=self.fetcher)
                return resolver.resolve(ref.metric)
            else:
                return ref.metric
        elif ref.metric_id is not None:
            # Fetch by ID
            metric_or_variant = self.fetcher(ref.metric_id)

            if isinstance(metric_or_variant, SemanticMetricVariant):
                # Compile variant
                from cortex.core.compiler.resolver import VariantResolver

                resolver = VariantResolver(fetcher=self.fetcher)
                return resolver.resolve(metric_or_variant)
            else:
                return metric_or_variant
        else:
            # Should never happen due to MetricRef validator
            raise ValueError("MetricRef has neither metric_id nor metric")

    def _validate_compatibility(
        self, primary: SemanticMetric, combine: SemanticMetric
    ) -> None:
        """
        Validate that combine metric is compatible with primary.

        Args:
            primary: Primary metric
            combine: Combine metric

        Raises:
            IncompatibleSourceError: If metrics are incompatible
        """
        # Check that they're in the same environment
        if primary.environment_id != combine.environment_id:
            raise IncompatibleSourceError(
                primary.name,
                combine.name,
                f"Different environment_id: {primary.environment_id} vs {combine.environment_id}",
            )

        # Check that they're in the same data model
        if primary.data_model_id != combine.data_model_id:
            raise IncompatibleSourceError(
                primary.name,
                combine.name,
                f"Different data_model_id: {primary.data_model_id} vs {combine.data_model_id}",
            )

        # Check that they use the same data source (optional but recommended)
        if (
            primary.data_source_id is not None
            and combine.data_source_id is not None
            and primary.data_source_id != combine.data_source_id
        ):
            # This is a warning rather than an error - might be intentional
            # for cross-database queries (if supported by the backend)
            pass

    def _get_dimension_names(self, metric: SemanticMetric) -> List[str]:
        """
        Get list of dimension names from a metric.

        Args:
            metric: SemanticMetric to extract dimension names from

        Returns:
            List of dimension names
        """
        if metric.dimensions is None:
            return []
        return [d.name for d in metric.dimensions]
