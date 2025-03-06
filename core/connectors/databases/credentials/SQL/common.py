from core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from core.types.databases import DataSourceTypes
from core.types.telescope import TSModel


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
