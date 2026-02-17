"""
Variant resolver for composable metrics system.

This module implements the VariantResolver class which resolves SemanticMetricVariants
into fully-resolved SemanticMetrics by:
- Following the source chain (handling variant-of-variant)
- Applying component overrides (include/exclude/replace/add)
- Merging derivations from source and variant
- Inheriting non-overridable fields
- Building composition for multi-source metrics
"""

from typing import Set, Optional, List
from uuid import UUID
from copy import deepcopy

from cortex.core.semantics.metrics.metric import SemanticMetric, MetricRef
from cortex.core.semantics.metrics.variant import SemanticMetricVariant
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.semantics.joins import SemanticJoin
from cortex.core.semantics.order_sequences import SemanticOrderSequence
from cortex.core.compiler.protocols import MetricFetcher
from cortex.core.compiler.exceptions import (
    CircularReferenceError,
    MaxDepthExceededError,
)


class VariantResolver:
    """
    Resolves SemanticMetricVariants into fully-resolved SemanticMetrics.

    The resolver handles the complete resolution process:
    1. Circular reference detection
    2. Depth guard (prevents chains > MAX_DEPTH)
    3. Recursive source resolution
    4. Component filtering via include whitelist
    5. Override application (exclude -> replace -> add)
    6. Derivation merging
    7. Non-overridable field inheritance
    8. Scalar field overrides
    9. Multi-source composition (combine)

    Resolution order: inherit → include → exclude → replace → add
    """

    MAX_DEPTH = 10

    def __init__(self, fetcher: MetricFetcher):
        """
        Initialize the resolver with a metric fetcher.

        Args:
            fetcher: Protocol for fetching metrics by ID
        """
        self.fetcher = fetcher

    def resolve(self, variant: SemanticMetricVariant) -> SemanticMetric:
        """
        Resolve a variant into a fully-resolved SemanticMetric.

        Args:
            variant: The variant to resolve

        Returns:
            Fully-resolved SemanticMetric ready for execution

        Raises:
            CircularReferenceError: If a circular reference is detected
            MaxDepthExceededError: If source chain depth exceeds MAX_DEPTH
        """
        return self._resolve_recursive(variant, seen=set(), depth=0)

    def _resolve_recursive(
        self,
        variant: SemanticMetricVariant,
        seen: Set[UUID],
        depth: int,
    ) -> SemanticMetric:
        """
        Recursively resolve a variant into a SemanticMetric.

        Args:
            variant: The variant to resolve
            seen: Set of variant IDs already seen in this chain (for cycle detection)
            depth: Current depth in the resolution chain

        Returns:
            Fully-resolved SemanticMetric

        Raises:
            CircularReferenceError: If a circular reference is detected
            MaxDepthExceededError: If depth exceeds MAX_DEPTH
        """
        # Step 1 - Circular ref + depth guard
        if variant.id in seen:
            # Circular reference detected - build the chain for error message
            chain = list(seen) + [variant.id]
            raise CircularReferenceError(chain)

        if depth >= self.MAX_DEPTH:
            raise MaxDepthExceededError(depth, self.MAX_DEPTH)

        # Add this variant to the seen set for cycle detection
        seen = seen | {variant.id}  # Create new set to avoid mutation

        # Step 2 - Fetch source
        # Resolve variant.source (MetricRef) to get the actual metric/variant
        source_metric_or_variant = self._fetch_metric(variant.source)

        # Step 3 - If source is variant, recurse
        if isinstance(source_metric_or_variant, SemanticMetricVariant):
            # Source is itself a variant - resolve it recursively
            base = self._resolve_recursive(
                source_metric_or_variant, seen=seen, depth=depth + 1
            )
        else:
            # Source is a base SemanticMetric - use it as-is
            base = source_metric_or_variant

        # Step 4 - Apply include whitelist
        # If variant.include is specified, filter base components to only those listed
        if variant.include is not None:
            base = self._apply_include_whitelist(base, variant.include)

        # Step 5 - Apply overrides: exclude -> replace -> add
        # Deep copy base to avoid mutations during override application
        resolved = deepcopy(base)

        if variant.overrides is not None:
            # Apply exclude (remove components by name)
            if variant.overrides.exclude is not None:
                exclude = variant.overrides.exclude
                resolved.measures = self._apply_exclude(
                    resolved.measures, exclude.measures
                )
                resolved.dimensions = self._apply_exclude(
                    resolved.dimensions, exclude.dimensions
                )
                resolved.filters = self._apply_exclude(
                    resolved.filters, exclude.filters
                )
                resolved.joins = self._apply_exclude(resolved.joins, exclude.joins)

            # Apply replace (replace components by name)
            if variant.overrides.replace is not None:
                replace = variant.overrides.replace
                if replace.measures is not None:
                    resolved.measures = self._apply_replace(
                        resolved.measures, replace.measures
                    )
                if replace.dimensions is not None:
                    resolved.dimensions = self._apply_replace(
                        resolved.dimensions, replace.dimensions
                    )
                if replace.filters is not None:
                    resolved.filters = self._apply_replace(
                        resolved.filters, replace.filters
                    )
                if replace.joins is not None:
                    resolved.joins = self._apply_replace(
                        resolved.joins, replace.joins
                    )
                if replace.order is not None:
                    resolved.order = self._apply_replace(
                        resolved.order, replace.order
                    )

            # Apply add (append new components)
            if variant.overrides.add is not None:
                add = variant.overrides.add
                if add.measures is not None:
                    resolved.measures = self._apply_add(
                        resolved.measures, add.measures
                    )
                if add.dimensions is not None:
                    resolved.dimensions = self._apply_add(
                        resolved.dimensions, add.dimensions
                    )
                if add.filters is not None:
                    resolved.filters = self._apply_add(resolved.filters, add.filters)
                if add.joins is not None:
                    resolved.joins = self._apply_add(resolved.joins, add.joins)
                if add.order is not None:
                    resolved.order = self._apply_add(resolved.order, add.order)

        # Step 6 - Merge derivations
        # Combine base.derivations + variant.derivations
        merged_derivations = []
        if base.derivations is not None:
            merged_derivations.extend(base.derivations)
        if variant.derivations is not None:
            merged_derivations.extend(variant.derivations)
        resolved.derivations = merged_derivations if merged_derivations else None

        # Step 7 - Validate and inherit non-overridable fields
        # Variants must belong to the same environment/data_model/data_source as their source
        if variant.environment_id != base.environment_id:
            raise IncompatibleSourceError(
                f"Variant '{variant.name}' (environment={variant.environment_id}) "
                f"cannot reference source in different environment ({base.environment_id})"
            )
        if variant.data_model_id != base.data_model_id:
            raise IncompatibleSourceError(
                f"Variant '{variant.name}' (data_model={variant.data_model_id}) "
                f"cannot reference source with different data model ({base.data_model_id})"
            )
        if variant.data_source_id is not None and base.data_source_id is not None:
            if variant.data_source_id != base.data_source_id:
                raise IncompatibleSourceError(
                    f"Variant '{variant.name}' (data_source={variant.data_source_id}) "
                    f"cannot reference source with different data source ({base.data_source_id})"
                )

        # Inherit non-overridable fields (already validated to match)
        resolved.environment_id = base.environment_id
        resolved.data_model_id = base.data_model_id
        resolved.data_source_id = base.data_source_id

        # Step 8 - Apply scalar overrides
        # Apply variant.overrides scalar field overrides if present
        if variant.overrides is not None:
            if variant.overrides.table_name is not None:
                resolved.table_name = variant.overrides.table_name
            if variant.overrides.limit is not None:
                resolved.limit = variant.overrides.limit
            if variant.overrides.grouped is not None:
                resolved.grouped = variant.overrides.grouped
            if variant.overrides.ordered is not None:
                resolved.ordered = variant.overrides.ordered

        # Step 9 - If variant has combine, resolve composition
        if variant.combine is not None and len(variant.combine) > 0:
            # Use composer to build CompositionSource list
            from cortex.core.compiler.composer import CTEComposer

            composer = CTEComposer(fetcher=self.fetcher)
            resolved.composition = composer.compose(resolved, variant.combine)
        else:
            resolved.composition = None

        # Step 10 - Build and return resolved SemanticMetric
        # Copy variant's own metadata fields
        resolved.name = variant.name
        resolved.alias = variant.alias
        resolved.description = variant.description
        resolved.version = variant.version
        resolved.public = variant.public
        resolved.cache = variant.cache
        resolved.refresh = variant.refresh
        resolved.parameters = variant.parameters
        resolved.meta = variant.meta
        resolved.created_at = variant.created_at
        resolved.updated_at = variant.updated_at

        # Use variant's ID as the resolved metric's ID
        resolved.id = variant.id

        return resolved

    def _fetch_metric(self, ref: MetricRef) -> SemanticMetric | SemanticMetricVariant:
        """
        Fetch a metric from a MetricRef.

        Args:
            ref: MetricRef containing either metric_id or inline metric

        Returns:
            The referenced metric (either SemanticMetric or SemanticMetricVariant)
        """
        if ref.metric is not None:
            # Inline metric definition
            return ref.metric
        elif ref.metric_id is not None:
            # Fetch by ID using the provided fetcher
            return self.fetcher(ref.metric_id)
        else:
            # Should never happen due to MetricRef validator
            raise ValueError("MetricRef has neither metric_id nor metric")

    def _apply_include_whitelist(
        self,
        base: SemanticMetric,
        include: object,  # IncludedComponents from overrides module
    ) -> SemanticMetric:
        """
        Apply include whitelist to filter base components.

        If include is specified, only components whose names are in the whitelist
        will be kept. If include is None, all components are kept.

        Args:
            base: The base metric with components to filter
            include: IncludedComponents whitelist

        Returns:
            SemanticMetric with filtered components
        """
        # Deep copy base to avoid mutation
        filtered = deepcopy(base)

        # Filter measures
        if include.measures is not None and filtered.measures is not None:
            filtered.measures = [
                m for m in filtered.measures if m.name in include.measures
            ]

        # Filter dimensions
        if include.dimensions is not None and filtered.dimensions is not None:
            filtered.dimensions = [
                d for d in filtered.dimensions if d.name in include.dimensions
            ]

        # Filter filters
        if include.filters is not None and filtered.filters is not None:
            filtered.filters = [
                f for f in filtered.filters if f.name in include.filters
            ]

        # Filter joins
        if include.joins is not None and filtered.joins is not None:
            filtered.joins = [
                j for j in filtered.joins if j.name in include.joins
            ]

        return filtered

    def _apply_exclude(
        self,
        components: Optional[List],
        exclude_names: Optional[List[str]],
    ) -> Optional[List]:
        """
        Remove components by name.

        Args:
            components: List of components (measures, dimensions, etc.)
            exclude_names: Names of components to exclude

        Returns:
            Filtered list with excluded components removed
        """
        if components is None or exclude_names is None:
            return components

        # Filter out components whose names are in the exclude list
        return [c for c in components if c.name not in exclude_names]

    def _apply_replace(
        self,
        components: Optional[List],
        replace_components: Optional[List],
    ) -> Optional[List]:
        """
        Replace components by name.

        Args:
            components: List of existing components
            replace_components: List of replacement components (matched by name)

        Returns:
            List with replaced components
        """
        if components is None:
            # No existing components, treat as add
            return replace_components

        if replace_components is None:
            return components

        # Build a map of replacement components by name
        replace_map = {c.name: c for c in replace_components}

        # Replace matching components, keep non-matching ones
        result = []
        for component in components:
            if component.name in replace_map:
                # Replace with new component
                result.append(replace_map[component.name])
            else:
                # Keep existing component
                result.append(component)

        return result

    def _apply_add(
        self,
        components: Optional[List],
        add_components: Optional[List],
    ) -> Optional[List]:
        """
        Add new components.

        Args:
            components: List of existing components
            add_components: List of components to add

        Returns:
            List with added components appended
        """
        if add_components is None:
            return components

        if components is None:
            return add_components

        # Append new components to existing ones
        return components + add_components
