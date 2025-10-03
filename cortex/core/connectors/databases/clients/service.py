from cortex.core.connectors.databases.clients.SQL.common import (
    CommonProtocolSQLClient,
    DuckDBClient,
    SQLiteClient,
)
from cortex.core.connectors.databases.clients.factory.implementations import (
    BigQueryClientFactory,
    CommonProtocolSQLClientFactory,
    DuckDBClientFactory,
    SQLiteClientFactory,
)
from cortex.core.connectors.databases.clients.generator import DatabaseClientGenerator
from cortex.core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentialsFactory
from cortex.core.connectors.databases.credentials.SQL.common import (
    CommonProtocolSQLCredentialsFactory,
    DuckDBCredentialsFactory,
    SQLiteCredentialsFactory,
)
from cortex.core.connectors.databases.credentials.generator import DatabaseCredentialsGenerator
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class DBClientService(TSModel):

    @staticmethod
    def get_client(details: dict, db_type: DataSourceTypes):
        factory = None
        client = None
        creds = None
        if db_type in {DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL}:
            creds_factory = CommonProtocolSQLCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = CommonProtocolSQLClientFactory()
        elif db_type == DataSourceTypes.SQLITE:
            creds_factory = SQLiteCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = SQLiteClientFactory()
        elif db_type == DataSourceTypes.DUCKDB:
            creds_factory = DuckDBCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = DuckDBClientFactory()
        elif db_type == DataSourceTypes.BIGQUERY:
            creds_factory = BigQueryCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = BigQueryClientFactory()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        client = DatabaseClientGenerator().parse(factory=client_factory, credentials=creds)
        return client


if __name__ == '__main__':
    conn_details = {"host": 'localhost', "port": 5432, "username": 'root', "password": 'password',
                    "database": 'cortex'}
    connection: CommonProtocolSQLClient = DBClientService.get_client(details=conn_details, db_type=DataSourceTypes.POSTGRESQL)
    print("Client: ", connection)
    print(connection.connect())
    print(connection.query("SELECT * FROM checkpoint_blobs LIMIT 100"))

