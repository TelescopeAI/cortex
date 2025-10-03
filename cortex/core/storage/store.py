import os
import logging
from functools import cached_property
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.storage.sqlalchemy import BaseDBModel
from cortex.core.types.databases import DataSourceTypes
from cortex.core.utils.json import json_dumps


class CortexStorage:
    Base = BaseDBModel
    _instance: Optional['CortexStorage'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._env = _StorageEnv.from_environ()
            self._client = self._create_client()
            self._session_factory: Optional[sessionmaker] = None
            self.connection = self._client
            self._initialized = True

    @cached_property
    def client(self):
        self._client.connect()
        return self._client

    def get_session(self) -> Session:
        if self._session_factory is None:
            # Use the same engine as _sqlalchemy_engine to ensure consistency
            engine = self._sqlalchemy_engine
            self._session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        assert self._session_factory is not None
        return self._session_factory()

    def close_session(self, session: Session) -> None:
        session.close()

    def reflect_on_db(self):
        return BaseDBModel.metadata.reflect(self._sqlalchemy_engine)

    def create_all_tables(self) -> None:
        BaseDBModel.metadata.create_all(bind=self._sqlalchemy_engine)

    def drop_all_tables(self) -> None:
        BaseDBModel.metadata.drop_all(bind=self._sqlalchemy_engine)

    @cached_property
    def _sqlalchemy_engine(self) -> Engine:
        return create_engine(
            self._build_sqlalchemy_url(),
            poolclass=self._get_pool_class(),
        )

    def _get_pool_class(self):
        """Get the appropriate connection pool class based on database type and configuration."""
        if self._env.db_type == DataSourceTypes.SQLITE and self._env.in_memory:
            # Use StaticPool for in-memory SQLite to ensure all connections share the same database
            return StaticPool
        # For other database types, use the default pool class
        return None

    def _create_client(self):
        details = self._env.to_dict()
        return DBClientService.get_client(details=details, db_type=self._env.db_type)

    def _build_sqlalchemy_url(self) -> str:
        if self._env.db_type == DataSourceTypes.POSTGRESQL:
            return (
                f"postgresql+psycopg://{self._env.username}:{self._env.password}"
                f"@{self._env.host}:{self._env.port}/{self._env.database}"
            )
        if self._env.db_type == DataSourceTypes.MYSQL:
            return (
                f"mysql+pymysql://{self._env.username}:{self._env.password}"
                f"@{self._env.host}:{self._env.port}/{self._env.database}"
            )
        if self._env.db_type == DataSourceTypes.SQLITE:
            if self._env.in_memory:
                return "sqlite+pysqlite:///:memory:"
            from pathlib import Path
            sqlite_path = Path(str(self._env.file_path or "./cortex.db")).expanduser().resolve()
            return f"sqlite+pysqlite:///{sqlite_path.as_posix()}"
        if self._env.db_type == DataSourceTypes.DUCKDB:
            raise RuntimeError(
                "DuckDB SQLAlchemy sessions are temporarily disabled. Set CORTEX_DB_TYPE to 'sqlite' or 'postgresql'."
            )
        raise ValueError(f"Unsupported storage type: {self._env.db_type}")

    @property
    def db_url(self) -> str:
        return self._build_sqlalchemy_url()

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._initialized = False


class _StorageEnv:
    def __init__(self, *, db_type: DataSourceTypes, host: Optional[str], port: Optional[int], username: Optional[str],
                 password: Optional[str], database: Optional[str], file_path: Optional[str], in_memory: bool) -> None:
        self.db_type = db_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.file_path = file_path
        self.in_memory = in_memory

    @classmethod
    def from_environ(cls) -> "_StorageEnv":
        db_type = DataSourceTypes(ExecutionEnv.get_key("CORTEX_DB_TYPE", DataSourceTypes.POSTGRESQL.value))
        return cls(
            db_type=db_type,
            host = ExecutionEnv.get_key("CORTEX_DB_HOST"),
            port = int(ExecutionEnv.get_key("CORTEX_DB_PORT", "0")) or None,
            username = ExecutionEnv.get_key("CORTEX_DB_USERNAME"),
            password = ExecutionEnv.get_key("CORTEX_DB_PASSWORD"),
            database = ExecutionEnv.get_key("CORTEX_DB_NAME"),
            file_path = ExecutionEnv.get_key("CORTEX_DB_FILE"),
            in_memory = str(ExecutionEnv.get_key("CORTEX_DB_MEMORY", "false")).lower() == "true",
        )

    def to_dict(self) -> dict:
        data = {"dialect": self.db_type.value}
        if self.db_type in {DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL}:
            data.update(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
            )
        else:
            data.update(file_path=self.file_path, in_memory=self.in_memory)
        return data
