from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional

import duckdb

from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.credentials.SQL.common import DuckDBCredentials
from cortex.core.exceptions.SQLClients import CSQLInvalidQuery


class DuckDBClient(DatabaseClient):
    credentials: DuckDBCredentials
    connection: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> "DuckDBClient":
        db_name = ":memory:" if self.credentials.in_memory else self.credentials.file_path or ":memory:"
        connection = duckdb.connect(database=db_name, config=self.credentials.config or None)
        self.connection = connection
        return self

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_uri(self) -> str:
        return self._build_uri()

    @property
    def db_url(self) -> str:
        return self._build_uri()

    def _build_uri(self) -> str:
        # Produce a duckdb-engine compatible URL for Alembic/SQLAlchemy
        if self.credentials.in_memory:
            return "duckdb:///:memory:"
        from pathlib import Path
        file_path = self.credentials.file_path or "./cortex.duckdb"
        abs_path = Path(file_path).expanduser().resolve().as_posix()
        return f"duckdb:///{abs_path}"

    def query(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        try:
            if self.connection is None:
                self.connect()
            assert self.connection is not None
            return self.connection.execute(sql, params or {})
        except duckdb.Error as exc:
            raise CSQLInvalidQuery(exc) from exc

    def fetch_one(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Optional[Mapping[str, Any]]:
        result = self.query(sql, params)
        rows = result.fetchall()
        return dict(zip(result.description, rows[0])) if rows else None

    def fetch_all(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> list[Mapping[str, Any]]:
        result = self.query(sql, params)
        rows = result.fetchall()
        return [dict(zip(result.description, row)) for row in rows]

    def stream(self, sql: str, params: Optional[Mapping[str, Any]] = None, chunk_size: int = 1000) -> Iterator[list[Mapping[str, Any]]]:
        result = self.query(sql, params)
        while True:
            chunk = result.fetchmany(chunk_size)
            if not chunk:
                break
            yield [dict(zip(result.description, row)) for row in chunk]

    def get_schema(self):
        raise NotImplementedError("DuckDB schema introspection not yet implemented")

    def get_table_names(self, schema_name: Optional[str] = None) -> list[str]:
        result = self.fetch_all("SHOW TABLES")
        return [row["name"] for row in result]

    def get_column_info(self, table_name: str, schema_name: Optional[str] = None) -> list[Any]:
        raise NotImplementedError("DuckDB column introspection not yet implemented")

