from cortex.core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory


class DatabaseClientGenerator:

    def parse(self, factory: DatabaseClientFactory, credentials, **kwargs):
        return factory.create_client(credentials=credentials, **kwargs)

