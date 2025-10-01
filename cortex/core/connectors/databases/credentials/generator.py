from cortex.core.connectors.databases.credentials.factory import DatabaseCredentialsFactory
from cortex.core.types.telescope import TSModel


class DatabaseCredentialsGenerator(TSModel):

    def parse(self, factory: DatabaseCredentialsFactory, **kwargs) -> TSModel:
        creds = factory.get_creds(**kwargs)
        return creds


# if __name__ == '__main__':
#     sql_factory = CommonSQLCredentialsFactory()
#     bq_factory = BigQueryCredentialsFactory()
#     sql_creds = DatabaseCredentialsGenerator().parse(factory=sql_factory, host='localhost', port=5432, username='user',
#                                                      password='password', database='db', dialect='postgresql')
#     bq_creds = DatabaseCredentialsGenerator().parse(factory=bq_factory, project_id='project', dataset_id='dataset')
    # print("SQL Client: ", sql_creds.json())
    # print("BQ Client: ", bq_creds.json())
