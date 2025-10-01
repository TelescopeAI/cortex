from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, sessionmaker

from cortex.core.connectors.databases.SQL.Schema import get_sql_schema
from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.credentials.SQL.common import CommonProtocolSQLCredentials
from cortex.core.exceptions.SQLClients import CSQLInvalidQuery
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.sql_schema import ColumnSchema
from cortex.core.utils.json import json_dumps


class CommonProtocolSQLClient(DatabaseClient):
    credentials: CommonProtocolSQLCredentials
    engine: Optional[Engine] = None
    session_factory: Optional[sessionmaker] = None

    def connect(self) -> "CommonProtocolSQLClient":
        engine = create_engine(
            self._build_uri(),
            pool_size=50,
            max_overflow=10,
            json_serializer=json_dumps,
        )
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        self.client = engine.connect()
        return self

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
        if self.engine is not None:
            self.engine.dispose()

    def get_uri(self) -> str:
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

    def get_session(self) -> Session:
        if self.session_factory is None:
            self.connect()
        assert self.session_factory is not None
        return self.session_factory()

    def get_schema(self):
        return get_sql_schema(self._build_uri())

    def get_table_names(self, schema_name: Optional[str] = None) -> list[str]:
        if self.engine is None:
            self.connect()
        assert self.engine is not None
        inspector = inspect(self.engine)
        return inspector.get_table_names(schema=schema_name)

    def get_column_info(self, table_name: str, schema_name: Optional[str] = None) -> list[ColumnSchema]:
        if self.engine is None:
            self.connect()
        assert self.engine is not None
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name, schema=schema_name)
        column_schema: list[ColumnSchema] = []
        for column in columns:
            column_schema.append(
                ColumnSchema(
                    name=column["name"],
                    type=str(column["type"]).split("(")[0].upper(),
                    max_length=getattr(column["type"], "length", None),
                    precision=getattr(column["type"], "precision", None),
                    scale=getattr(column["type"], "scale", None),
                    nullable=column.get("nullable"),
                    default_value=str(column.get("default")) if column.get("default") is not None else None,
                )
            )
        return column_schema

    def _build_uri(self) -> str:
        dialect = self.credentials.dialect.value
        if self.credentials.dialect is DataSourceTypes.MYSQL:
            dialect = "mysql+pymysql"
        if self.credentials.dialect is DataSourceTypes.POSTGRESQL:
            dialect = "postgresql+psycopg"
        return (
            f"{dialect}://{self.credentials.username}:{self.credentials.password}"
            f"@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
        )

