from cortex.core.connectors.databases.clients.SQL.common import CommonSQLClient
from cortex.core.connectors.databases.clients.factory.implementations import CommonSQLClientFactory, BigQueryClientFactory
from cortex.core.connectors.databases.clients.generator import DatabaseClientGenerator
from cortex.core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentialsFactory
from cortex.core.connectors.databases.credentials.SQL.common import CommonSQLCredentialsFactory
from cortex.core.connectors.databases.credentials.generator import DatabaseCredentialsGenerator
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class DBClientService(TSModel):

    @staticmethod
    def get_client(details: dict, db_type: DataSourceTypes):
        factory = None
        client = None
        creds = None
        is_common_sql = db_type in [DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL, DataSourceTypes.ORACLE,
                                    DataSourceTypes.SQLITE]
        if is_common_sql:
            creds_factory = CommonSQLCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = CommonSQLClientFactory()
            details['dialect'] = details['dialect'].lower()
        if db_type == DataSourceTypes.BIGQUERY:
            creds_factory = BigQueryCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = BigQueryClientFactory()
        client = DatabaseClientGenerator().parse(factory=client_factory, credentials=creds)
        return client


if __name__ == '__main__':
    conn_details = {"host": 'localhost', "port": 5432, "username": 'root', "password": 'password',
                    "database": 'observer', "dialect": 'postgresql'}
    connection: CommonSQLClient = DBClientService.get_client(details=conn_details, db_type=DataSourceTypes.POSTGRESQL)
    print("Client: ", connection)
    print(connection.connect())
    print(connection.query("SELECT * FROM checkpoint_blobs LIMIT 100"))

