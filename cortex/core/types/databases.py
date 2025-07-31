from enum import Enum


class DataSourceTypes(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
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
