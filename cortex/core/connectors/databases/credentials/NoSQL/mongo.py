from cortex.core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from cortex.core.types.telescope import TSModel


class MongoDBCredentials(TSModel):
    host: str
    port: int


class MongoDBCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> MongoDBCredentials:
        return MongoDBCredentials(**kwargs)
