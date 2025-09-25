from cortex.core.connectors.databases.clients.NoSQL.mongo import MongoDBClient
from cortex.core.connectors.databases.clients.SQL.bigquery import BigQueryClient
from cortex.core.connectors.databases.clients.SQL.common_protocol import CommonProtocolSQLClient
from cortex.core.connectors.databases.clients.SQL.duckdb import DuckDBClient
from cortex.core.connectors.databases.clients.SQL.sqlite import SQLiteClient
from cortex.core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory
from cortex.core.connectors.databases.credentials.NoSQL.mongo import MongoDBCredentials
from cortex.core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentials
from cortex.core.connectors.databases.credentials.SQL.common import (
    CommonProtocolSQLCredentials,
    DuckDBCredentials,
    SQLiteCredentials,
)


class CommonProtocolSQLClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: CommonProtocolSQLCredentials) -> CommonProtocolSQLClient:
        return CommonProtocolSQLClient(credentials=credentials)


class SQLiteClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: SQLiteCredentials) -> SQLiteClient:
        return SQLiteClient(credentials=credentials)


class DuckDBClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: DuckDBCredentials) -> DuckDBClient:
        return DuckDBClient(credentials=credentials)


class BigQueryClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: BigQueryCredentials) -> BigQueryClient:
        return BigQueryClient(credentials=credentials)


class MongoClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: MongoDBCredentials) -> MongoDBClient:
        return MongoDBClient(credentials=credentials)