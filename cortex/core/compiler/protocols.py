"""
Protocols for the compiler module.

This module defines protocols that decouple the compiler from the database layer,
enabling dependency injection and testability.
"""

from typing import Protocol, Union
from uuid import UUID

from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.variant import SemanticMetricVariant


class MetricFetcher(Protocol):
    """
    Protocol for fetching metrics by ID.

    This decouples the compiler from the database layer, allowing different
    implementations (DB service, cache, test fixtures) to be injected.

    The fetcher must return either a SemanticMetric or SemanticMetricVariant,
    as variants can reference other variants as their source.
    """

    def __call__(
        self, metric_id: UUID
    ) -> Union[SemanticMetric, SemanticMetricVariant]:
        """
        Fetch a metric or variant by ID.

        Args:
            metric_id: UUID of the metric or variant to fetch

        Returns:
            Either a SemanticMetric or SemanticMetricVariant

        Raises:
            Exception: Implementation-specific exception if metric not found
        """
        ...
