from __future__ import annotations

from typing import Any, Iterator, Mapping, Optional, Protocol


class SQLClientProtocol(Protocol):
    def connect(self) -> SQLClientProtocol:
        ...

    def close(self) -> None:
        ...

    def query(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Any:
        ...

    def fetch_one(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> Optional[Mapping[str, Any]]:
        ...

    def fetch_all(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> list[Mapping[str, Any]]:
        ...

    def stream(self, sql: str, params: Optional[Mapping[str, Any]] = None, chunk_size: int = 1000) -> Iterator[list[Mapping[str, Any]]]:
        ...

    def get_schema(self) -> Any:
        ...

    def get_table_names(self, schema_name: Optional[str] = None) -> list[str]:
        ...

    def get_column_info(self, table_name: str, schema_name: Optional[str] = None) -> list[Any]:
        ...


class SessionProviderProtocol(Protocol):
    def get_session(self) -> Any:
        ...


class TransactionalProtocol(Protocol):
    def begin(self) -> Any:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

