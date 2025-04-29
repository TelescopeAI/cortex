from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.credentials.NoSQL.mongo import MongoDBCredentials
from cortex.core.connectors.databases.credentials.factory import DatabaseCredentialsFactory


class MongoDBClient(DatabaseClient):
    credentials: MongoDBCredentials

    def connect(self):
        pass

    def get_uri(self):
        pass

    def query(self):
        pass

    def get_schema(self):
        pass


class MongoDBCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> MongoDBCredentials:
        return MongoDBCredentials(**kwargs)
