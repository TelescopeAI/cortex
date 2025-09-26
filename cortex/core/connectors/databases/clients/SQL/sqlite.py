from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import sessionmaker

from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.credentials.SQL.common import SQLiteCredentials
from cortex.core.exceptions.SQLClients import CSQLInvalidQuery


class SQLiteClient(DatabaseClient):
    credentials: SQLiteCredentials
    engine: Optional[Engine] = None
    session_factory: Optional[sessionmaker] = None

    def connect(self) -> "SQLiteClient":
        engine = create_engine(
            self._build_uri(),
            connect_args={"check_same_thread": False},
        )
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        connection = engine.connect()
        for pragma, value in self.credentials.pragmas.items():
            connection.execute(text(f"PRAGMA {pragma} = {value}"))
        self.client = connection
        return self

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None

    def get_uri(self) -> str:
        return self._build_uri()

    @property
    def db_url(self) -> str:
        return self._build_uri()

    def query(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        try:
            if self.client is None:
                self.connect()
            assert self.client is not None
            result = self.client.execute(text(sql), params or {})
            try:
                return result.fetchall()
            finally:
                result.close()
        except DatabaseError as exc:
            raise CSQLInvalidQuery(exc) from exc

    def fetch_one(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Optional[Mapping[str, Any]]:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def fetch_all(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> list[Mapping[str, Any]]:
        if self.client is None:
            self.connect()
        assert self.client is not None
        result = self.client.execute(text(sql), params or {})
        try:
            return [dict(row) for row in result.mappings().all()]
        finally:
            result.close()

    def stream(self, sql: str, params: Optional[Mapping[str, Any]] = None, chunk_size: int = 1000) -> Iterator[list[Mapping[str, Any]]]:
        if self.client is None:
            self.connect()
        assert self.client is not None
        result = self.client.execute(text(sql), params or {})
        try:
            while True:
                chunk = result.mappings().fetchmany(chunk_size)
                if not chunk:
                    break
                yield [dict(row) for row in chunk]
        finally:
            result.close()

    def get_schema(self):
        inspector = inspect(self._ensure_engine())
        tables = []
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            tables.append({"name": table_name, "columns": columns})
        return tables

    def get_table_names(self, schema_name: Optional[str] = None) -> list[str]:
        inspector = inspect(self._ensure_engine())
        return inspector.get_table_names()

    def get_column_info(self, table_name: str, schema_name: Optional[str] = None) -> list[Any]:
        inspector = inspect(self._ensure_engine())
        return inspector.get_columns(table_name)

    def _build_uri(self) -> str:
        if self.credentials.in_memory:
            return "sqlite+pysqlite:///:memory:"
        if not self.credentials.file_path:
            return "sqlite+pysqlite:///:memory:"
        return f"sqlite+pysqlite:///{self.credentials.file_path}"

    def _ensure_engine(self) -> Engine:
        if self.engine is None:
            self.connect()
        assert self.engine is not None
        return self.engine

