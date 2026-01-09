from typing import Any, Dict, Optional

from pydantic import Field, model_validator

from cortex.core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class CommonProtocolSQLCredentials(TSModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    dialect: DataSourceTypes
    schema: Optional[str] = None  # Optional schema name for PostgreSQL tenant isolation

    @model_validator(mode="after")
    def validate_dialect(self) -> "CommonProtocolSQLCredentials":
        if self.dialect not in {DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL}:
            raise ValueError("CommonProtocolSQLCredentials supports only PostgreSQL or MySQL dialects")
        return self


class SQLiteCredentials(TSModel):
    dialect: DataSourceTypes = Field(default=DataSourceTypes.SQLITE)
    file_path: Optional[str] = None
    in_memory: bool = False
    pragmas: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self) -> "SQLiteCredentials":
        if not self.file_path and not self.in_memory:
            raise ValueError("SQLiteCredentials require either a file_path or in_memory=True")
        if self.file_path and self.in_memory:
            raise ValueError("SQLiteCredentials cannot specify both file_path and in_memory")
        return self


class DuckDBCredentials(TSModel):
    dialect: DataSourceTypes = Field(default=DataSourceTypes.DUCKDB)
    file_path: Optional[str] = None
    in_memory: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self) -> "DuckDBCredentials":
        if not self.file_path and not self.in_memory:
            raise ValueError("DuckDBCredentials require either a file_path or in_memory=True")
        if self.file_path and self.in_memory:
            raise ValueError("DuckDBCredentials cannot specify both file_path and in_memory")
        return self


class CommonProtocolSQLCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> CommonProtocolSQLCredentials:
        return CommonProtocolSQLCredentials(**kwargs)


class SQLiteCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> SQLiteCredentials:
        return SQLiteCredentials(**kwargs)


class DuckDBCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> DuckDBCredentials:
        return DuckDBCredentials(**kwargs)
