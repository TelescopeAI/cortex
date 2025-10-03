from typing import Optional
from cortex.core.preaggregations.compute.base import ComputeAdapter
from cortex.core.preaggregations.engines.capabilities import POSTGRES_CAPABILITIES
from cortex.core.preaggregations.models import (
    EngineCapabilities,
    EngineType,
    PreAggregationBuildOptions,
    PreAggregationSpec,
    PreAggregationBuildStrategy,
)
from cortex.core.preaggregations.service import PreAggregationService, _sanitize_identifier
from cortex.core.preaggregations import get_service
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.connectors.databases.clients.SQL.common import CommonProtocolSQLClient
from cortex.core.data.db.source_service import DataSourceCRUD
from cortex.core.types.databases import DataSourceTypes
from sqlalchemy import text


class PostgresComputeAdapter(ComputeAdapter):
    """Compute adapter for Postgres pre-aggregation builds.

    Uses MATERIALIZED VIEW or CTAS depending on `build.strategy`. For MVP, this
    executes raw statements via the shared LocalSession and does not handle
    atomic swaps or partitioned rebuilds.
    """
    def engine(self) -> EngineType:
        return EngineType.POSTGRES

    def capabilities(self) -> EngineCapabilities:
        return POSTGRES_CAPABILITIES

    def build_or_refresh(self, spec: PreAggregationSpec, build_options: Optional[PreAggregationBuildOptions] = None) -> None:
        print(f"[PREAGG] Starting build_or_refresh for spec: {spec.id}")
        print(f"[PREAGG] Spec details: name={spec.name}, metric_id={spec.metric_id}")
        print(f"[PREAGG] Source: data_source_id={spec.source.data_source_id}, table={spec.source.table}, schema={spec.source.schema}")
        
        # Minimal MVP: build CTAS or refresh MV if present
        sql = self._build_sql(spec)
        
        # Get database connection details from data source
        print(f"[PREAGG] Fetching data source: {spec.source.data_source_id}")
        data_source = DataSourceCRUD.get_data_source(spec.source.data_source_id)
        if not data_source:
            raise ValueError(f"Data source not found: {spec.source.data_source_id}")
        
        print(f"[PREAGG] Found data source: {data_source.name} (type: {data_source.source_type})")
        
        # Extract connection details from the config
        config = data_source.config
        conn_details = {
            "host": config.get("host"),
            "port": config.get("port"),
            "username": config.get("username"),
            "password": config.get("password"),
            "database": config.get("database"),
            "dialect": data_source.source_type.value.lower()  # Use the source_type enum
        }
        # Log only safe connection details (never username or password)
        print(f"[PREAGG] Connection details: host={conn_details['host']}, port={conn_details['port']}, database={conn_details['database']}")
        
        client: CommonProtocolSQLClient = DBClientService.get_client(
            details=conn_details, 
            db_type=DataSourceTypes.POSTGRESQL
        )
        
        try:
            # Connect to the database
            # Log only safe connection details (never username or password)
            print(f"[PREAGG] Connecting to database: {conn_details['host']}:{conn_details['port']}/{conn_details['database']}")
            client.connect()
            print(f"[PREAGG] Successfully connected to database")
            
            # Execute statements inside an explicit transaction; autocommit is not available
            orm_client = client.client
            trans = orm_client.begin()
            try:
                for i, stmt in enumerate(sql):
                    try:
                        print(f"[PREAGG] Executing statement {i+1}/{len(sql)}: {stmt}")
                        orm_client.execute(text(stmt))
                        print(f"[PREAGG] Statement {i+1} executed successfully")
                    except Exception as stmt_exc:
                        print(f"[PREAGG] Error executing statement {i+1}: {stmt_exc}")
                        print(f"[PREAGG] Failed statement: {stmt}")
                        raise stmt_exc
                trans.commit()
                print(f"[PREAGG] Transaction committed for {len(sql)} statements")
            except Exception as exc_tx:
                print(f"[PREAGG] Transaction error, rolling back: {exc_tx}")
                try:
                    trans.rollback()
                except Exception as rb_exc:
                    print(f"[PREAGG] Rollback failed: {rb_exc}")
                raise
                
        except Exception as exc:
            print(f"[PREAGG] Database operation failed: {exc}")
            raise exc
        finally:
            # Ensure connection is closed
            try:
                if hasattr(client, 'close'):
                    client.close()
                    print(f"[PREAGG] Database connection closed")
            except Exception as close_exc:
                print(f"[PREAGG] Error closing connection: {close_exc}")

    def _build_sql(self, spec: PreAggregationSpec) -> list[str]:
        # Sanitize the name to be a valid SQL identifier
        raw_name = spec.name or f"mv_{spec.metric_id}"
        name = _sanitize_identifier(raw_name)
        print(f"[PREAGG] Building SQL for spec: {spec.id}")
        print(f"[PREAGG] Raw name: {raw_name} -> Sanitized name: {name}")
        
        # Basic schema qualification if provided
        if spec.source.schema:
            schema = _sanitize_identifier(spec.source.schema)
            name = f"{schema}.{name}"
            print(f"[PREAGG] Schema qualified name: {name}")
        
        select_sql = self._select_sql_from_spec(spec)
        print(f"[PREAGG] Generated SELECT SQL: {select_sql}")
        
        if spec.build and spec.build.strategy == PreAggregationBuildStrategy.MATERIALIZED_VIEW:
            sql_statements = [
                f'CREATE MATERIALIZED VIEW IF NOT EXISTS "{name}" AS {select_sql}',
                f'REFRESH MATERIALIZED VIEW "{name}"',
            ]
            print(f"[PREAGG] Using MATERIALIZED_VIEW strategy with {len(sql_statements)} statements")
            return sql_statements
        
        # Default to CTAS full rebuild
        sql_statements = [
            f'DROP TABLE IF EXISTS "{name}"',
            f'CREATE TABLE "{name}" AS {select_sql}',
        ]
        print(f"[PREAGG] Using CTAS strategy with {len(sql_statements)} statements")
        return sql_statements

    def _select_sql_from_spec(self, spec: PreAggregationSpec) -> str:
        print(f"[PREAGG] Generating SELECT SQL for spec: {spec.id}")
        
        if spec.build and spec.build.select_sql:
            print(f"[PREAGG] Using provided select_sql: {spec.build.select_sql}")
            return spec.build.select_sql
        
        # Try to generate SELECT via service fallback; if unavailable use base table
        try:
            print(f"[PREAGG] Attempting to generate rollup SELECT via service")
            # Use global service to derive SELECT from spec and metric context if available
            service = get_service()
            # For MVP we cannot fetch the metric here; build from spec only
            base_select = service.generate_rollup_select(metric=None, spec_id=spec.id)  # type: ignore[arg-type]
            if base_select:
                print(f"[PREAGG] Generated rollup SELECT: {base_select}")
                return base_select
            else:
                print(f"[PREAGG] Service returned empty SELECT, falling back to base table")
        except Exception as exc:
            print(f"[PREAGG] Service generation failed: {exc}, falling back to base table")
        
        # Sanitize table name for SQL safety
        table_name = _sanitize_identifier(spec.source.table)
        if spec.source.schema:
            schema_name = _sanitize_identifier(spec.source.schema)
            fallback_sql = f'SELECT * FROM "{schema_name}"."{table_name}"'
        else:
            fallback_sql = f'SELECT * FROM "{table_name}"'
        
        print(f"[PREAGG] Using fallback SELECT: {fallback_sql}")
        return fallback_sql


