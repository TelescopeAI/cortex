from typing import Any

from sqlalchemy import create_engine, inspect, text

from cortex.core.connectors.databases.SQL.Schema import get_sql_schema
from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentials


class BigQueryClient(DatabaseClient):
    credentials: BigQueryCredentials
    engine: Any = None

    def query(self, sql, params=None):
        if self.client is None:
            self.get_connection()
        conn = self.client

        if params is None:
            result = conn.execute(text(sql))
        else:
            result = conn.execute(text(sql), **params)
        fetched_results = result.fetchall()
        result.close()
        return fetched_results

    def get_schema(self):
        schema = get_sql_schema(self.get_uri())
        return schema

    def get_uri(self, uri_only: bool = False):
        conn_string = (f'bigquery://{self.credentials.project_id}')
        if self.credentials.dataset_id:
            conn_string += f'/{self.credentials.dataset_id}'

        if uri_only:
            return conn_string
        # conn_string += f'?credentials_path={"/Users/zinomex/Desktop/Telescope/observer/credentials/key.json"}'
        conn_string += f'?credentials_info={self.credentials.service_account_details}'
        return conn_string

    def connect(self):
        conn_string = self.get_uri()
        engine = create_engine(conn_string, credentials_info=self.credentials.service_account_details)
        conn = engine.connect()
        self.client = conn
        return self

    def get_engine(self):
        conn_string = self.get_uri(uri_only=True)
        self.engine = create_engine(conn_string)
        return self.engine

    def get_table_names(self, dataset_name: str):
        # Get all the contents of the table with the table name using the SQLAlchemy engine
        inspector = inspect(self.engine)
        schemas = inspector.get_schema_names()
        tables = []
        for schema in schemas:
            # print("schema: %s" % schema)
            if schema == dataset_name:
                tables = inspector.get_table_names(schema=schema)
        return tables
