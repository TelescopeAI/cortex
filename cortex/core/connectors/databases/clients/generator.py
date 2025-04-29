from cortex.core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory
from cortex.core.types.telescope import TSModel


class DatabaseClientGenerator(TSModel):

    def parse(self, factory: DatabaseClientFactory, credentials: TSModel, **kwargs) -> TSModel:
        creds = factory.create_client(credentials=credentials, **kwargs)
        return creds

