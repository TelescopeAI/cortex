from typing import List, Optional
import re
from uuid import uuid4, UUID
from datetime import datetime

from cortex.core.preaggregations.compute.base import ComputeAdapter
from cortex.core.preaggregations.engines.registry import EngineRegistry
from cortex.core.preaggregations.models import (
    EngineType,
    PreAggregationPlanResult,
    PreAggregationSpec,
    PreAggregationStatus,
)
from cortex.core.preaggregations.planner import CoveragePreAggregationPlanner
from cortex.core.preaggregations.registry import InMemoryPreAggregationRegistry
from cortex.core.preaggregations.resolvers.registry import ResolverRegistry
from cortex.core.preaggregations.scheduler.base import SchedulerAdapter
from cortex.core.query.engine.bindings.rollup_binding import RollupBindingModel
from cortex.core.types.databases import DataSourceTypes
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.cache.manager import QueryCacheManager
from cortex.core.cache.factory import get_cache_storage
from cortex.core.config.models.cache import CacheConfig
from cortex.core.data.db.metric_service import MetricService


class PreAggregationService:
    """Orchestration service for pre-aggregations.

    Responsibilities:
    - Registry CRUD for specs
    - Planning coverage for incoming queries
    - Build/refresh execution via compute adapters
    - Scheduling integration and status tracking
    - Optional cache invalidation post-refresh
    """
    def __init__(
        self,
        registry: Optional[InMemoryPreAggregationRegistry] = None,
        planner: Optional[CoveragePreAggregationPlanner] = None,
        engine_registry: Optional[EngineRegistry] = None,
        compute_adapters: Optional[List[ComputeAdapter]] = None,
        resolver_registry: Optional[ResolverRegistry] = None,
        scheduler: Optional[SchedulerAdapter] = None,
    ) -> None:
        self.registry = registry or InMemoryPreAggregationRegistry()
        self.planner = planner or CoveragePreAggregationPlanner()
        self.engine_registry = engine_registry or EngineRegistry()
        self.compute_adapters = compute_adapters or []
        self.resolver_registry = resolver_registry or ResolverRegistry()
        self.scheduler = scheduler
        self._status_by_spec: dict[str, PreAggregationStatus] = {}

    def upsert_spec(self, spec: PreAggregationSpec) -> None:
        # Prefill missing values from metric if not present
        spec = self._prefill_missing_values(spec)
        self.registry.upsert_spec(spec)

    def list_specs(self, metric_id: Optional[UUID] = None) -> List[PreAggregationSpec]:
        return list(self.registry.list_specs(metric_id=metric_id))

    def get_spec(self, spec_id: str) -> Optional[PreAggregationSpec]:
        return self.registry.get_spec(spec_id)

    def delete_spec(self, spec_id: str) -> bool:
        """Delete a spec and return True if it existed, False if not found."""
        spec = self.registry.get_spec(spec_id)
        if spec:
            self.registry.delete_spec(spec_id)
            return True
        return False

    def plan(
        self,
        metric,
        requested_dimensions: List[str],
        requested_measures: List[str],
    ) -> PreAggregationPlanResult:
        specs = list(self.registry.list_specs(metric_id=metric.id))
        return self.planner.plan(metric=metric, requested_dimensions=requested_dimensions, requested_measures=requested_measures, filters=None, specs=specs)

    def generate_rollup_select(self, metric, spec_id: str) -> Optional[str]:
        spec = self.registry.get_spec(spec_id)
        if not spec:
            return None
        # Build a binding model for observability and future serve-path reuse
        qualified_table = f'"{spec.source.schema}"."{spec.source.table}"' if spec.source.schema else f'"{spec.source.table}"'
        binding = RollupBindingModel(
            qualified_table=qualified_table,
            dimension_columns={},
            measure_columns={},
            time_bucket_columns={},
            pre_aggregation_spec_id=uuid4(),  # placeholder until persisted
        )
        # Use the dimensions and measures directly from the spec
        dims: list[SemanticDimension] = list(spec.dimensions or [])
        measures: list[SemanticMeasure] = list(spec.measures or [])

        if metric is not None:
            tmp_metric = metric.model_copy(update={
                "table_name": spec.source.table,
                "measures": measures,
                "dimensions": dims,
            })
        else:
            from cortex.core.semantics.metrics.metric import SemanticMetric
            tmp_metric = SemanticMetric(
                data_model_id=uuid4(),
                name=_sanitize_identifier(spec.name or f"preagg_{spec.metric_id}"),
                table_name=spec.source.table,
                measures=measures,
                dimensions=dims,
            )
        # Import here to avoid circular import
        from cortex.core.query.engine.factory import QueryGeneratorFactory
        generator = QueryGeneratorFactory.create_generator(tmp_metric, DataSourceTypes.POSTGRESQL)
        # Note: The standard generator is used for build SELECT; binding not required at build phase yet
        return generator.generate_query(parameters=None, limit=None, offset=None, grouped=True)


    def build_or_refresh(self, spec_id: str, dry_run: bool = False) -> PreAggregationStatus:
        spec = self.registry.get_spec(spec_id)
        if spec is None:
            return PreAggregationStatus(spec_id=spec_id, error="SPEC_NOT_FOUND")

        # Prefill missing values from metric if not present
        spec = self._prefill_missing_values(spec)

        start = datetime.utcnow()
        try:
            if dry_run:
                status = PreAggregationStatus(spec_id=spec_id, last_refreshed_at=None, duration_ms=0, row_count=None, bytes_written=None, dry_run=True)
                self._status_by_spec[spec_id] = status
                return status

            adapter = self._resolve_compute_adapter(spec.source.engine)
            adapter.build_or_refresh(spec)
            end = datetime.utcnow()
            status = PreAggregationStatus(
                spec_id=spec_id,
                last_refreshed_at=end,
                duration_ms=int((end - start).total_seconds() * 1000),
            )
            self._status_by_spec[spec_id] = status
            # Cache invalidation: bump namespace by deleting keys tagged with this spec (future pub/sub); for now clear cache
            try:
                cache_cfg = CacheConfig.from_env()
                storage = get_cache_storage(cache_cfg)
                storage.clear()
            except Exception as exc:
                pass
            return status
        except Exception as exc:
            end = datetime.utcnow()
            status = PreAggregationStatus(
                spec_id=spec_id,
                last_refreshed_at=None,
                duration_ms=int((end - start).total_seconds() * 1000),
                error=str(exc),
            )
            self._status_by_spec[spec_id] = status
            return status

    def _prefill_missing_values(self, spec: PreAggregationSpec) -> PreAggregationSpec:
        """Prefill missing values in DataSourceRef from metric if not present.
        
        This ensures that the DataSourceRef has valid data_source_id and table name
        for building pre-aggregations, even if they weren't provided during spec creation.
        """
        needs_update = False
        updated_source = spec.source.model_copy()
        
        # Try to get the metric to populate missing values
        try:
            metric_service = MetricService()
            metric = metric_service.get_metric_by_id(spec.metric_id)
            if metric:
                # Populate data_source_id if missing
                if not updated_source.data_source_id and metric.data_source_id:
                    updated_source.data_source_id = metric.data_source_id
                    needs_update = True
                
                # Populate table name if missing
                if not updated_source.table and metric.table_name:
                    updated_source.table = metric.table_name
                    needs_update = True
                
                # Populate engine if missing (default to postgres)
                if not updated_source.engine:
                    updated_source.engine = EngineType.POSTGRES
                    needs_update = True
                    
        except Exception:
            # If we can't fetch the metric, continue with the original spec
            pass
        
        # Return updated spec if any changes were made
        if needs_update:
            updated_spec = spec.model_copy()
            updated_spec.source = updated_source
            return updated_spec
        
        return spec

    def _resolve_compute_adapter(self, engine: EngineType) -> ComputeAdapter:
        for adapter in self.compute_adapters:
            if adapter.engine() == engine:
                return adapter
        # Fallbacks can be improved later by registry/factory
        raise ValueError(f"No compute adapter registered for engine: {engine}")

    def get_status(self, spec_id: str) -> Optional[PreAggregationStatus]:
        return self._status_by_spec.get(spec_id)

    def schedule(self, spec_id: str) -> bool:
        if not self.scheduler:
            return False
        spec = self.registry.get_spec(spec_id)
        if not spec:
            return False
        self.scheduler.schedule_refresh(spec)
        return True

    def cancel(self, spec_id: str) -> bool:
        if not self.scheduler:
            return False
        self.scheduler.cancel(spec_id)
        return True


def _sanitize_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")
