import os
import logging
from contextvars import ContextVar
from functools import cached_property
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.connectors.databases.clients.service import DBClientService
from cortex.core.storage.sqlalchemy import BaseDBModel
from cortex.core.types.databases import DataSourceTypes
from cortex.core.utils.json import json_dumps
from urllib.parse import quote_plus

# Context variable to hold tenant-specific storage
_tenant_storage: ContextVar[Optional['CortexStorage']] = ContextVar('_tenant_storage', default=None)


class CortexStorage:
    Base = BaseDBModel
    _instance: Optional['CortexStorage'] = None
    _initialized = False

    def __new__(cls, _force_new=False):
        """Create singleton or new instance based on _force_new flag."""
        if _force_new:
            # Create a new instance for tenant-specific storage
            return object.__new__(cls)
        
        # Singleton behavior (for migrations, backward compat)
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, env: Optional['_StorageEnv'] = None):
        """
        Initialize storage.
        
        Args:
            env: Optional _StorageEnv with tenant-specific credentials.
                 If None, reads from environment (singleton behavior).
        """
        # Skip re-initialization for tenant instances
        if hasattr(self, '_is_tenant_instance') and self._is_tenant_instance:
            return
            
        if not self._initialized:
            self._env = env or _StorageEnv.from_environ()
            self._client = self._create_client()
            self._session_factory: Optional[sessionmaker] = None
            self.connection = self._client
            
            if env is not None:
                # Mark as tenant instance (don't share singleton state)
                self._is_tenant_instance = True
            else:
                self._initialized = True

    @cached_property
    def client(self):
        self._client.connect()
        return self._client

    def get_session(self) -> Session:
        """Get a database session, respecting tenant context."""
        # Check if there's a tenant-specific storage in context
        tenant_storage = _tenant_storage.get()
        if tenant_storage is not None and tenant_storage is not self:
            # Delegate to tenant storage
            return tenant_storage.get_session()
        
        if self._session_factory is None:
            # Use the same engine as _sqlalchemy_engine to ensure consistency
            engine = self._sqlalchemy_engine
            self._session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        assert self._session_factory is not None
        
        session = self._session_factory()
        
        # If Postgres and schema is specified, set search_path
        if self._env.db_type == DataSourceTypes.POSTGRESQL and hasattr(self._env, '_schema') and self._env._schema:
            session.execute(text(f"SET search_path TO {self._env._schema}, public"))
            session.commit()
        
        return session

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
        # Get pool settings from _StorageEnv
        pool_size = getattr(self._env, '_pool_size', 5)
        max_overflow = getattr(self._env, '_max_overflow', 10)
        
        # Build engine kwargs
        engine_kwargs = {
            'json_serializer': json_dumps,
        }
        
        pool_class = self._get_pool_class()
        if pool_class is not None:
            engine_kwargs['poolclass'] = pool_class
        
        # Only add pool_size and max_overflow for non-StaticPool (SQLite in-memory doesn't support it)
        if pool_class is None or pool_class != StaticPool:
            engine_kwargs['pool_size'] = pool_size
            engine_kwargs['max_overflow'] = max_overflow
        
        return create_engine(
            self._build_sqlalchemy_url(),
            **engine_kwargs
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
            # URL-encode username and password to handle special characters
            username = quote_plus(str(self._env.username)) if self._env.username else ""
            # Ensure password is not None, empty, or masked
            password_value = self._env.password
            if password_value is None or password_value == "" or password_value == "***":
                logger_obj = logging.getLogger(__name__)
                logger_obj.error(f"Invalid password value when building database URL! Password: {repr(password_value)}")
                raise ValueError(
                    f"Password is None, empty, or masked ('***'). "
                    f"Cannot build database URL. Check that password is properly set in credentials."
                )
            password = quote_plus(str(password_value))
            
            # Use configured dialect (psycopg or pg8000)
            driver = self._env._dialect
            logger_obj = logging.getLogger(__name__)
            logger_obj.debug(f"[CortexStorage] Building URL with dialect: {driver}")
            
            return (
                f"postgresql+{driver}://{username}:{password}"
                f"@{self._env.host}:{self._env.port}/{self._env.database}"
            )
        if self._env.db_type == DataSourceTypes.MYSQL:
            # URL-encode username and password to handle special characters
            username = quote_plus(str(self._env.username)) if self._env.username else ""
            password = quote_plus(str(self._env.password)) if self._env.password else ""
            return (
                f"mysql+pymysql://{username}:{password}"
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
    def with_credentials(cls, *, 
                        host: str,
                        port: int,
                        username: str,
                        password: str,
                        database: str,
                        schema: Optional[str] = None,
                        db_type: DataSourceTypes = DataSourceTypes.POSTGRESQL,
                        dialect: str = 'psycopg',
                        pool_size: int = 5,
                        max_overflow: int = 10) -> 'CortexStorage':
        """
        Create a tenant-specific CortexStorage instance with explicit credentials.
        
        This method creates a NEW instance (not the singleton) configured for a specific tenant.
        Use this in Humane to create per-org storage.
        
        Args:
            host: Database host (can be PgBouncer host for connection pooling)
            port: Database port
            username: Database user (dedicated per org for security)
            password: Database password
            database: Database name
            schema: Postgres schema name for tenant isolation (e.g., "org_550e8400e29b41d4a716446655440000")
            db_type: Database type (default: PostgreSQL)
            dialect: Database dialect driver (e.g., 'psycopg' or 'pg8000' for PostgreSQL)
            pool_size: SQLAlchemy connection pool size (default: 5, use 2 with PgBouncer)
            max_overflow: Additional connections beyond pool_size (default: 10, use 1 with PgBouncer)
        
        Returns:
            CortexStorage instance for the tenant
        """
        env = _StorageEnv(
            db_type=db_type,
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            file_path=None,
            in_memory=False,
            dialect=dialect,
        )
        
        # Store schema and pool config for later use
        env._schema = schema
        env._pool_size = pool_size
        env._max_overflow = max_overflow
        
        # Create new instance (bypass singleton) and initialize it
        instance = object.__new__(cls)
        instance.__init__(env=env)
        return instance
    
    @classmethod
    def set_tenant_context(cls, storage: Optional['CortexStorage']) -> None:
        """
        Set tenant-specific storage for the current request context.
        
        Call this in Humane middleware with the org's storage instance.
        All subsequent CortexStorage().get_session() calls will use this storage.
        """
        _tenant_storage.set(storage)

    @classmethod
    def clear_tenant_context(cls) -> None:
        """Clear tenant context (e.g., at end of request)."""
        _tenant_storage.set(None)

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._initialized = False


class _StorageEnv:
    def __init__(self, *, db_type: DataSourceTypes, host: Optional[str], port: Optional[int], username: Optional[str],
                 password: Optional[str], database: Optional[str], file_path: Optional[str], in_memory: bool,
                 dialect: str = 'psycopg') -> None:
        self.db_type = db_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.file_path = file_path
        self.in_memory = in_memory
        self._dialect = dialect
        # Multi-tenancy fields (optional, for tenant-specific storage)
        self._schema: Optional[str] = None
        self._pool_size: int = 5
        self._max_overflow: int = 10

    @classmethod
    def from_environ(cls) -> "_StorageEnv":
        db_type = DataSourceTypes(ExecutionEnv.get_key("CORTEX_DB_TYPE", DataSourceTypes.POSTGRESQL.value))
        dialect = ExecutionEnv.get_key("CORTEX_DB_DIALECT", "psycopg")
        return cls(
            db_type=db_type,
            host = ExecutionEnv.get_key("CORTEX_DB_HOST"),
            port = int(ExecutionEnv.get_key("CORTEX_DB_PORT", "0")) or None,
            username = ExecutionEnv.get_key("CORTEX_DB_USERNAME"),
            password = ExecutionEnv.get_key("CORTEX_DB_PASSWORD"),
            database = ExecutionEnv.get_key("CORTEX_DB_NAME"),
            file_path = ExecutionEnv.get_key("CORTEX_DB_FILE"),
            in_memory = str(ExecutionEnv.get_key("CORTEX_DB_MEMORY", "false")).lower() == "true",
            dialect = dialect,
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
