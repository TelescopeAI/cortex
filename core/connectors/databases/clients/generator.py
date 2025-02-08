from core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory
from core.types.telescope import TSModel


class DatabaseClientGenerator(TSModel):

    def parse(self, factory: DatabaseClientFactory, credentials: TSModel, **kwargs) -> TSModel:
        creds = factory.create_client(credentials=credentials, **kwargs)
        return creds

