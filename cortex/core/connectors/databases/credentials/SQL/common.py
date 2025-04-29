from cortex.core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class CommonSQLCredentials(TSModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    dialect: DataSourceTypes


class CommonSQLCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> CommonSQLCredentials:
        return CommonSQLCredentials(**kwargs)
