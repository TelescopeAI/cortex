from typing import Optional

from core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from core.types.telescope import TSModel


class BigQueryCredentials(TSModel):
    project_id: str
    dataset_id: Optional[str] = None
    service_account_details: dict


class BigQueryCredentialsFactory(DatabaseCredentialsFactory):
    def get_creds(self, **kwargs) -> BigQueryCredentials:
        return BigQueryCredentials(**kwargs)
