"""Data source related services."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from cortex.core.cache.factory import get_cache_storage
from cortex.core.cache.keys import build_cache_key, build_query_signature
from cortex.core.cache.manager import QueryCacheManager
from cortex.core.config.models.cache import CacheConfig
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD


class DataSourceSchemaService:
    """Service for retrieving and caching data source schemas."""

    def __init__(self, cache_config: Optional[CacheConfig] = None) -> None:
        self._explicit_config = cache_config

    def get_schema(self, data_source_id: UUID) -> Dict[str, Any]:
        """Return the schema for a data source, using cache when enabled."""

        cache_config = self._explicit_config or CacheConfig.from_env()
        cache_enabled = bool(cache_config.enabled)
        cache_manager: Optional[QueryCacheManager] = None
        cache_key: Optional[str] = None

        model_service = DataModelService()
        try:
            data_source = DataSourceCRUD.get_data_source(data_source_id)

            environment_id = getattr(data_source, "environment_id", None)
            workspace_id = None
            if environment_id:
                environment = EnvironmentCRUD.get_environment(environment_id)
                workspace_id = getattr(environment, "workspace_id", None)

            data_model_ids = self._collect_data_model_ids(model_service, data_source_id)

            connection_details = dict(data_source.config or {})
            source_type_value = getattr(data_source.source_type, "value", data_source.source_type)
            if source_type_value:
                connection_details.setdefault("dialect", source_type_value)

            signature_payload = self._build_signature_payload(
                cache_config=cache_config,
                workspace_id=workspace_id,
                environment_id=environment_id,
                data_source_id=data_source.id,
                data_model_ids=data_model_ids,
                source_type=data_source.source_type.value,
                updated_at=getattr(data_source, "updated_at", None),
            )

            if cache_enabled:
                cache_manager = QueryCacheManager(get_cache_storage(cache_config))
                cache_signature = build_query_signature(signature_payload)
                cache_key = build_cache_key(cache_signature)
                cached_response = cache_manager.get(cache_key)
                if cached_response is not None:
                    return cached_response

            client = DBClientService.get_client(details=connection_details, db_type=data_source.source_type)
            client.connect()
            schema = client.get_schema()
            schema_payload = schema.model_dump() if hasattr(schema, "model_dump") else schema

            response = {
                "data_source_id": str(data_source_id),
                "data_source_name": data_source.name,
                "source_type": data_source.source_type.value,
                "schema": schema_payload,
            }

            if cache_enabled and cache_manager and cache_key:
                ttl_seconds = 3600
                cache_manager.set(cache_key, response, ttl_seconds)

            return response
        finally:
            model_service.close()

    def _collect_data_model_ids(self, model_service: DataModelService, data_source_id: UUID) -> List[str]:
        # Since data models no longer have data_source_id, we need to get data model IDs
        # through metrics that are associated with this data source
        metric_service = MetricService()
        try:
            # Get all metrics for this data source
            metrics = metric_service.get_metrics_by_data_source(data_source_id)
            ids: List[str] = []
            for metric in metrics:
                model_id = getattr(metric, "data_model_id", None)
                if model_id:
                    ids.append(str(model_id))
            return sorted(set(ids))
        finally:
            metric_service.close()

    def _build_signature_payload(
        self,
        *,
        cache_config: CacheConfig,
        workspace_id: Optional[UUID],
        environment_id: Optional[UUID],
        data_source_id: UUID,
        data_model_ids: List[str],
        source_type: str,
        updated_at: Optional[datetime],
    ) -> Dict[str, Any]:
        return {
            "namespace": "data_source_schema",
            "workspace_id": str(workspace_id) if workspace_id else None,
            "environment_id": str(environment_id) if environment_id else None,
            "data_source_id": str(data_source_id),
            "data_model_ids": data_model_ids,
            "source_type": source_type,
            "source_updated_at": updated_at.astimezone(timezone.utc).isoformat(timespec="seconds") if updated_at else None,
        }


