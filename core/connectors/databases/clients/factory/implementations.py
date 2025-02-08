from core.connectors.databases.clients.NoSQL.mongo import MongoDBClient
from core.connectors.databases.clients.SQL.bigquery import BigQueryClient
from core.connectors.databases.clients.SQL.common import CommonSQLClient
from core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory
from core.connectors.databases.credentials.NoSQL.mongo import MongoDBCredentials
from core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentials
from core.connectors.databases.credentials.SQL.common import CommonSQLCredentials


class CommonSQLClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: CommonSQLCredentials) -> CommonSQLClient:
        return CommonSQLClient(credentials=credentials)


class BigQueryClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: BigQueryCredentials) -> BigQueryClient:
        return BigQueryClient(credentials=credentials)


class MongoClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: MongoDBCredentials) -> MongoDBClient:
        return MongoDBClient(credentials=credentials)