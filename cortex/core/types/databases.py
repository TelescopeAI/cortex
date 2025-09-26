from enum import Enum

from sqlalchemy import JSON, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.types import TypeDecorator


class DataSourceTypes(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    DUCKDB = "duckdb"
    ORACLE = "oracle"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"
    MONGODB = "mongodb"
    DYNAMODB = "dynamodb"
    COUCHBASE = "couchbase"


class DataSourceCatalog(str, Enum):
    DATABASE = "DATABASE"
    API = "API"
    FILE = "FILE"


class JSONType(TypeDecorator):
    cache_ok = True
    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class ArrayType(TypeDecorator):
    cache_ok = True
    impl = JSON

    def __init__(self, item_type=Text(), **kwargs):
        super().__init__(**kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(self.item_type))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return list(value) if isinstance(value, (list, tuple)) else value


class DatabaseTypeResolver:
    @staticmethod
    def json_type():
        return JSONType()

    @staticmethod
    def array_type(item_type=Text()):
        return ArrayType(item_type)
