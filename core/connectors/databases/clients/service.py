from core.connectors.databases.clients.SQL.bigquery import BigQueryClient
from core.connectors.databases.clients.SQL.common import CommonSQLClient
from core.connectors.databases.clients.factory.implementations import CommonSQLClientFactory, BigQueryClientFactory
from core.connectors.databases.clients.generator import DatabaseClientGenerator
from core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentialsFactory
from core.connectors.databases.credentials.SQL.common import CommonSQLCredentialsFactory
from core.connectors.databases.credentials.generator import DatabaseCredentialsGenerator
from core.types.databases import DatabaseTypes
from core.types.telescope import TSModel


class DBClientService(TSModel):

    @staticmethod
    def get_client(details: dict, db_type: DatabaseTypes):
        factory = None
        client = None
        creds = None
        is_common_sql = db_type in [DatabaseTypes.POSTGRESQL, DatabaseTypes.MYSQL, DatabaseTypes.ORACLE,
                                    DatabaseTypes.SQLITE]
        if is_common_sql:
            creds_factory = CommonSQLCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = CommonSQLClientFactory()
            details['dialect'] = details['dialect'].lower()
        if db_type == DatabaseTypes.BIGQUERY:
            creds_factory = BigQueryCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = BigQueryClientFactory()
        client = DatabaseClientGenerator().parse(factory=client_factory, credentials=creds)
        return client


if __name__ == '__main__':
    conn_details = {"host": 'localhost', "port": 5432, "username": 'root', "password": 'password',
                    "database": 'observer', "dialect": 'postgresql'}
    connection: CommonSQLClient = DBClientService.get_client(details=conn_details, db_type=DatabaseTypes.POSTGRESQL)
    print("Client: ", connection)
    print(connection.connect())
    print(connection.query("SELECT * FROM checkpoint_blobs LIMIT 5"))

