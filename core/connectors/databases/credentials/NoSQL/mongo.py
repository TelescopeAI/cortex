from core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from core.types.telescope import TSModel


class MongoDBCredentials(TSModel):
    host: str
    port: int


class MongoDBCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> MongoDBCredentials:
        return MongoDBCredentials(**kwargs)
