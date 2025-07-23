from typing import Any, List

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import DatabaseError

from cortex.core.connectors.databases.SQL.Schema import get_sql_schema
from cortex.core.connectors.databases.clients.base import DatabaseClient
from cortex.core.connectors.databases.clients.factory.abstracts import DatabaseClientFactory
from cortex.core.connectors.databases.credentials.SQL.common import CommonSQLCredentials
from cortex.core.exceptions.SQLClients import CSQLInvalidQuery
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.sql_schema import ColumnSchema


class SQLDatabaseClientFactory(DatabaseClientFactory):
    def create_client(self, credentials: CommonSQLCredentials) -> CommonSQLCredentials:
        return CommonSQLCredentials(credentials)


class CommonSQLClient(DatabaseClient):
    credentials: CommonSQLCredentials
    engine: Any = None

    def connect(self):
        conn_string = self.get_uri()
        engine = create_engine(conn_string)
        self.engine = engine
        conn = engine.connect()
        self.client = conn
        return self

    def query(self, sql, params=None):
        try:
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
        except DatabaseError as e:
            raise CSQLInvalidQuery(e)

    def get_uri(self):
        dialect = self.credentials.dialect
        dialect_str = dialect.value
        if dialect is DataSourceTypes.MYSQL:
            dialect_str = "mysql+pymysql"
        if dialect is DataSourceTypes.POSTGRESQL:
            dialect_str = "postgresql+psycopg"
        conn_string = f"{dialect_str}://{self.credentials.username}:{self.credentials.password}@{self.credentials.host}:{self.credentials.port}/{self.credentials.database}"
        return conn_string

    def get_schema(self):
        schema = get_sql_schema(self.get_uri())
        return schema

    def get_table_names(self, schema_name: str = "public") -> List[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names(schema=schema_name)

    def get_examples(self, tables: List[str], schema_name: str = "public", count: int = 5) -> List[str]:
        examples = []
        for table in tables:
            query = f"SELECT * FROM {table} LIMIT {count}"
            try:
                result = self.query(query)
                examples.append(result)
            except CSQLInvalidQuery:
                examples.append([])
        return examples

    def get_column_info(self, table_name: str, schema_name: str = "public") -> List[ColumnSchema]:
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name, schema=schema_name)

        column_schema: List[ColumnSchema] = []
        for col in columns:
            # Extract detailed type information
            col_type = col['type']
            type_name = str(col_type).split('(')[0].upper()
            
            # Extract type-specific attributes
            max_length = None
            precision = None
            scale = None
            
            if hasattr(col_type, 'length') and col_type.length is not None:
                max_length = col_type.length
            if hasattr(col_type, 'precision') and col_type.precision is not None:
                precision = col_type.precision
            if hasattr(col_type, 'scale') and col_type.scale is not None:
                scale = col_type.scale
            
            # Get nullable and default information
            nullable = col.get('nullable')
            default_value = str(col['default']) if col.get('default') is not None else None
            
            column = ColumnSchema(
                name=col['name'],
                type=type_name,
                max_length=max_length,
                precision=precision,
                scale=scale,
                nullable=nullable,
                default_value=default_value
            )
            column_schema.append(column)
        return column_schema
