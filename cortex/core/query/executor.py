from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from pydantic import Field

from cortex.core.data.modelling.model import DataModel
from cortex.core.query.engine.factory import QueryGeneratorFactory
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.metrics.modifiers import (
    MetricModifier,
    MetricModifiers,
    apply_metric_modifiers,
)
from cortex.core.types.databases import DataSourceTypes
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.utils.parsesql import convert_sqlalchemy_rows_to_dict
from cortex.core.types.telescope import TSModel
from cortex.core.query.context import MetricContext
from cortex.core.query.history.logger import QueryHistory, QueryCacheMode
from cortex.core.query.db.service import QueryHistoryCRUD
from cortex.core.cache.keys import build_query_signature, derive_time_bucket, build_cache_key
from cortex.core.cache.manager import QueryCacheManager
from cortex.core.cache.factory import get_cache_storage
from cortex.core.config.models.cache import CacheConfig
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.core.semantics.cache import CachePreference
from cortex.core.preaggregations import get_service, load_env_config
from cortex.core.preaggregations.service import _sanitize_identifier
from cortex.core.query.engine.bindings.rollup_binding import RollupBindingModel


class QueryExecutor(TSModel):
    """
    Enhanced query executor with logging capabilities and metric execution.
    Handles query generation, execution, result processing, and audit logging.
    """
    
    # Use QueryHistory for logging
    query_history: QueryHistory = Field(default_factory=QueryHistory)
    
    def execute_metric(
        self, 
        metric: SemanticMetric,
        data_model: DataModel,
        parameters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        source_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
        context_id: Optional[str] = None,
        grouped: Optional[bool] = None,
        cache_preference: Optional[CachePreference] = None,
        modifiers: Optional[MetricModifiers] = None,
        preview: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Execute a specific metric from a data model with comprehensive logging.
        
        Args:
            metric: The metric to execute
            data_model: The data model containing the metric
            parameters: Optional parameters for query execution
            limit: Optional limit on result rows
            offset: Optional offset for pagination
            source_type: Database source type (defaults to PostgreSQL)
            context_id: Optional context identifier
            grouped: Optional override for grouping
            cache_preference: Optional cache preferences
            modifiers: Optional metric modifiers
            preview: If True, generate query without executing or caching
            
        Returns:
            Dict with success status, data, metadata, and optional errors
        """
        start_time = datetime.now()

        cache_mode: QueryCacheMode = QueryCacheMode.UNCACHED
        cache_signature: Optional[str] = None
        cache_enabled = False
        cache_manager: Optional[QueryCacheManager] = None
        cache_key: Optional[str] = None
        cached_payload: Optional[Dict[str, Any]] = None
        
        meta = {
            "source_type": source_type.value,
            "limit": limit,
            "offset": offset,
            "grouped": grouped
        }
        
        # Apply metric modifiers up-front so planning, generation and formatting see updated components
        resolved_metric = apply_metric_modifiers(metric, modifiers)

        try:
            # Pre-aggregations: attempt planner routing if enabled and specs exist
            try:
                preagg_env = load_env_config()
                if preagg_env.enabled:
                    preagg_service = get_service()
                    requested_dimensions = [d.query for d in (resolved_metric.dimensions or [])]
                    requested_measures = [m.query for m in (resolved_metric.measures or [])]
                    
                    # Debug: Check how many specs are available
                    available_specs = preagg_service.list_specs(metric_id=metric.id)
                    print(f"[PREAGG] Available specs for metric {metric.id}: {len(available_specs)}")
                    print(f"[PREAGG] Requested dimensions: {requested_dimensions}")
                    print(f"[PREAGG] Requested measures: {requested_measures}")
                    
                    plan_result = preagg_service.plan(metric, requested_dimensions=requested_dimensions, requested_measures=requested_measures)
                    print(f"[PREAGG] Plan result: covered={plan_result.covered}, spec_id={plan_result.spec_id}, reason={plan_result.reason}")
                    
                    if plan_result.covered and plan_result.spec_id:
                        # Route to rollup: select only needed columns using the standard generator with a binding
                        spec = preagg_service.registry.get_spec(plan_result.spec_id)
                        if spec and (spec.name or spec.metric_id):
                            object_name = _sanitize_identifier(spec.name or f"mv_{spec.metric_id}")
                            qualified = f'"{spec.source.schema}"."{object_name}"' if getattr(spec.source, "schema", None) else f'"{object_name}"'
                            # Build a minimal binding mapping from dimension/measure names to canonical columns
                            dimension_map = {d: f"{d}" for d in ([dim for dim in (resolved_metric.dimensions or []) if dim.query] and [dim.query for dim in (resolved_metric.dimensions or [])])}
                            measure_map = {m: f"{m}" for m in ([ms for ms in (resolved_metric.measures or []) if ms.query] and [ms.query for ms in (resolved_metric.measures or [])])}
                            binding = RollupBindingModel(
                                qualified_table=qualified,
                                dimension_columns=dimension_map,
                                measure_columns=measure_map,
                                time_bucket_columns={},
                                pre_aggregation_spec_id=None,
                            ).to_query_binding()
                            # Use the standard generator but attach binding so FROM and SELECT map to rollup
                            generator = QueryGeneratorFactory.create_generator(resolved_metric, source_type)
                            generator.binding = binding  # type: ignore[attr-defined]
                            generated_query = generator.generate_query(parameters, limit, offset, grouped)
                            query_results = self._execute_database_query(generated_query, metric.data_source_id)
                            end_time = datetime.now()
                            duration = (end_time - start_time).total_seconds() * 1000
                            return {
                                "success": True,
                                "data": query_results,
                                "metadata": {
                                    "metric_id": str(metric.id),
                                    "duration": duration,
                                    "row_count": len(query_results) if query_results else 0,
                                    "query": generated_query,
                                    "parameters": parameters,
                                    "pre_aggregation_spec_id": plan_result.spec_id,
                                    "rollup_binding": {
                                        "qualified_table": qualified,
                                        "dimension_columns": dimension_map,
                                        "measure_columns": measure_map,
                                    },
                                }
                            }
            except Exception:
                raise

            # Initialize caching if enabled and we have enough context to key it
            try:
                cfg = CacheConfig.from_env()
                env_enabled = bool(cfg.enabled)
                metric_enabled = bool(getattr(getattr(metric, 'cache', None), 'enabled', True))
                request_enabled = None
                if cache_preference is not None and hasattr(cache_preference, 'enabled'):
                    request_enabled = bool(getattr(cache_preference, 'enabled'))
                cache_enabled = bool(request_enabled) if request_enabled is not None else (env_enabled and metric_enabled)
                # Disable cache for preview mode
                if preview:
                    cache_enabled = False
                print(f"[CORTEX CACHE] resolve enabled -> env={env_enabled} metric={metric_enabled} request={request_enabled} preview={preview} final={cache_enabled}")

                if cache_enabled and metric.data_source_id:
                    ds = DataSourceCRUD.get_data_source(metric.data_source_id)
                    environment_id = getattr(ds, "environment_id", None)
                    workspace_id = None
                    if environment_id:
                        env = EnvironmentCRUD.get_environment(environment_id)
                        workspace_id = getattr(env, "workspace_id", None)
                    # derive bucket from pre-aggregation policy
                    bucket = derive_time_bucket(start_time, getattr(metric, 'refresh', None))
                    signature_payload = {
                        "workspace_id": str(workspace_id) if workspace_id else None,
                        "environment_id": str(environment_id) if environment_id else None,
                        "data_model_id": str(data_model.id),
                        "metric_id": str(metric.id),
                        "parameters": parameters or {},
                        "context_id": context_id,
                        "source_type": source_type.value,
                        "grouped": grouped,
                        "limit": limit,
                        "offset": offset,
                        "bucket": bucket,
                        "metric_version": getattr(metric, "version", None),
                        "compiled_query": getattr(metric, "compiled_query", None),
                        "modifiers": [m.model_dump(mode="json", exclude_none=True) for m in modifiers] if modifiers else None,
                    }
                    cache_signature = build_query_signature(signature_payload)
                    cache_key = build_cache_key(cache_signature)
                    cache_manager = QueryCacheManager(get_cache_storage(cfg))
                    print(f"[CORTEX CACHE] prepared key={cache_key} sig={cache_signature} backend={cfg.backend}")
                    cached_payload = cache_manager.get(cache_key)
                    if cached_payload is not None:
                        cache_mode = QueryCacheMode.CACHE_HIT
                        lookup_duration = (datetime.now() - start_time).total_seconds() * 1000
                        try:
                            log_entry = self.query_history.log_success(
                                metric_id=metric.id,
                                data_model_id=data_model.id,
                                query=(cached_payload.get("metadata", {}) or {}).get("query", ""),
                                duration=lookup_duration,
                                row_count=int((cached_payload.get("metadata", {}) or {}).get("row_count", 0)),
                                parameters=parameters,
                                context_id=context_id,
                                meta=meta,
                                cache_mode=cache_mode,
                                query_hash=cache_signature,
                            )
                            QueryHistoryCRUD.add_query_log(log_entry)
                        except Exception:
                            pass
                        result_metadata = (cached_payload.get("metadata", {}) or {}).copy()
                        result_metadata["duration"] = lookup_duration
                        result_metadata.setdefault("metric_id", str(metric.id))
                        print(f"[CORTEX CACHE] HIT key={cache_key} sig={cache_signature} duration_ms={lookup_duration:.2f}")
                        return {
                            "success": True,
                            "data": cached_payload.get("data"),
                            "metadata": result_metadata,
                        }
            except Exception as e:
                cache_enabled = False
                print(f"[CORTEX CACHE] read path error: {e}")

            enhanced_parameters = self._enhance_parameters_with_context(parameters, context_id)
            query_generator = QueryGeneratorFactory.create_generator(resolved_metric, source_type)
            generated_query = query_generator.generate_query(enhanced_parameters, limit, offset, grouped)
            
            # If preview mode, return early with generated query
            if preview:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds() * 1000
                return {
                    "success": True,
                    "data": None,
                    "metadata": {
                        "metric_id": str(metric.id),
                        "query": generated_query,
                        "parameters": parameters,
                        "preview": True,
                        "duration": duration,
                    }
                }
            
            query_results = self._execute_database_query(generated_query, metric.data_source_id)
            
            all_formats = OutputProcessor.collect_semantic_formatting(
                measures=resolved_metric.measures,
                dimensions=resolved_metric.dimensions,
                filters=resolved_metric.filters
            )
            
            flat_formats = []
            for format_list in all_formats.values():
                if format_list:
                    flat_formats.extend(format_list)
            
            if flat_formats:
                transformed_results = OutputProcessor.process_output_formats(
                    query_results, 
                    flat_formats
                )
            else:
                transformed_results = query_results
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000

            # Cache write
            if cache_enabled and cache_manager and cache_key and cache_signature:
                # Resolve TTL: request cache.ttl > metric.cache.ttl > env default
                req_ttl = getattr(cache_preference, 'ttl', None) if cache_preference else None
                metric_ttl = getattr(getattr(metric, 'cache', None), 'ttl', None)
                ttl_seconds = int(req_ttl if req_ttl is not None else (metric_ttl if metric_ttl is not None else cfg.ttl_seconds_default))
                cache_value = {
                    "data": transformed_results,
                    "metadata": {
                        "metric_id": str(metric.id),
                        "duration": duration,
                        "row_count": len(transformed_results) if transformed_results else 0,
                        "query": generated_query,
                        "parameters": parameters,
                    },
                    "stored_at": end_time.isoformat(),
                    "query_hash": cache_signature,
                    "metric_version": getattr(metric, "version", None),
                    "schema_version": "1",
                }
                try:
                    cache_manager.set(cache_key, cache_value, ttl_seconds)
                    cache_mode = QueryCacheMode.CACHE_MISS_EXECUTED
                except Exception:
                    cache_mode = QueryCacheMode.UNCACHED
                print(f"[CORTEX CACHE] MISS/STORE key={cache_key} sig={cache_signature} ttl={ttl_seconds}s rows={len(transformed_results) if transformed_results else 0}")
            
            log_entry = self.query_history.log_success(
                metric_id=metric.id,
                data_model_id=data_model.id,
                query=generated_query,
                duration=duration,
                row_count=len(transformed_results) if transformed_results else 0,
                parameters=parameters,
                context_id=context_id,
                meta=meta,
                cache_mode=cache_mode,
                query_hash=cache_signature,
            )
            
            try:
                QueryHistoryCRUD.add_query_log(log_entry)
            except Exception as db_error:
                print(f"Failed to persist query log to database: {db_error}")
            
            return {
                "success": True,
                "data": transformed_results,
                "metadata": {
                    "metric_id": str(metric.id),
                    "duration": duration,
                    "row_count": len(transformed_results) if transformed_results else 0,
                    "query": generated_query,
                    "parameters": parameters
                }
            }
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            log_entry = self.query_history.log_failure(
                metric_id=metric.id,
                data_model_id=data_model.id,
                query=generated_query if 'generated_query' in locals() else "",
                duration=duration,
                error_message=str(e),
                parameters=parameters,
                context_id=context_id,
                meta=meta,
                cache_mode=QueryCacheMode.UNCACHED,
                query_hash=cache_signature,
            )
            
            try:
                QueryHistoryCRUD.add_query_log(log_entry)
            except Exception as db_error:
                print(f"Failed to persist failed query log to database: {db_error}")
            
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "metric_id": str(metric.id),
                    "duration": duration,
                    "query": generated_query if 'generated_query' in locals() else "",
                    "parameters": parameters
                }
            }
 
    
    def _execute_database_query(self, query: str, data_source_id: UUID) -> List[Dict[str, Any]]:
        """
        Execute the actual database query using the specified data source.

        Args:
            query: SQL query to execute.
            data_source_id: The ID of the data source to use for the query.

        Returns:
            A list of dictionaries representing the query results.
        """
        # 1. Fetch the data source details
        data_source = DataSourceCRUD.get_data_source(data_source_id)

        # 2. Get the appropriate database client
        client = DBClientService.get_client(
            details=data_source.config,
            db_type=data_source.source_type
        )

        # 3. Connect, execute the query, and fetch results
        client.connect()
        results = client.query(query)

        # 4. Convert results to a list of dictionaries
        return convert_sqlalchemy_rows_to_dict(results)
    
    def _enhance_parameters_with_context(self, parameters: Optional[Dict[str, Any]], context_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Enhance parameters with context-based values from consumer properties.
        
        Args:
            parameters: Original parameters dictionary
            context_id: Context identifier in format <TYPE>_<UNIQUEID> or <TYPE>_<ID1>_<ID2>
            
        Returns:
            Enhanced parameters dictionary with context values substituted
        """
        if not context_id:
            return parameters
        
        try:
            # Parse the context_id
            context = MetricContext.parse(context_id)
            
            # Get consumer properties from context
            consumer_properties = context.get_consumer_properties()
            
            if not consumer_properties:
                return parameters
            
            # Create enhanced parameters by merging original parameters with consumer properties
            enhanced_parameters = parameters.copy() if parameters else {}
            
            # Merge consumer properties into enhanced parameters for $CORTEX_ substitution
            enhanced_parameters.update(consumer_properties)
            
            return enhanced_parameters
            
        except Exception as e:
            print(f"Error enhancing parameters with context {context_id}: {e}")
            return parameters
    

    
    def get_query_log(self, limit: Optional[int] = None):
        """
        Get the query execution log.
        
        Args:
            limit: Optional limit on number of entries to return
            
        Returns:
            List of QueryLog objects
        """
        return self.query_history.get_recent(limit)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get aggregated execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        return self.query_history.stats()
    
    def clear_query_log(self) -> None:
        """Clear the query execution log."""
        self.query_history.clear() 

    def _derive_ttl_seconds(self, refresh_key, default_ttl: int) -> int:
        """Compute TTL seconds from refresh_key; fallback to default."""
        try:
            from cortex.core.semantics.refresh_keys import RefreshKeyType
            if not refresh_key:
                return int(default_ttl)
            if getattr(refresh_key, "type", None) == RefreshKeyType.EVERY and getattr(refresh_key, "every", None):
                parts = str(refresh_key.every).strip().split()
                if len(parts) != 2:
                    return int(default_ttl)
                amount = int(parts[0])
                unit = parts[1].lower()
                if unit.startswith("hour"):
                    return amount * 3600
                if unit.startswith("minute"):
                    return amount * 60
                if unit.startswith("day"):
                    return amount * 86400
                return int(default_ttl)
            # For sql/max, use default for now
            return int(default_ttl)
        except Exception:
            return int(default_ttl)