from enum import Enum


class DatabaseTypes(Enum):
    POSTGRESQL = 'postgresql'
    MYSQL = 'mysql'
    SQLITE = 'sqlite'
    ORACLE = 'oracle'
    BIGQUERY = 'bigquery'
    SNOWFLAKE = 'snowflake'
    REDSHIFT = 'redshift'
    MONGODB = 'mongodb'