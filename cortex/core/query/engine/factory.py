from cortex.core.query.engine.base import BaseQueryGenerator
from cortex.core.query.engine.modules.sql.postgres import PostgresQueryGenerator
from cortex.core.query.engine.modules.sql.mysql import MySQLQueryGenerator
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.databases import DataSourceTypes


class QueryGeneratorFactory:
    @staticmethod
    def create_generator(metric: SemanticMetric, source_type: DataSourceTypes) -> BaseQueryGenerator:
        """
        Factory method to create an appropriate query generator based on dialect.

        Args:
            metric: The semantic metric to generate a query for
            source_type: The database source implementation that should be used to generate the query

        Returns:
            An instance of the appropriate query generator
        """
        if source_type == DataSourceTypes.POSTGRESQL:
            return PostgresQueryGenerator(metric=metric, source_type=source_type)
        elif source_type == DataSourceTypes.MYSQL:
            return MySQLQueryGenerator(metric=metric, source_type=source_type)
        # elif dialect == "bigquery":
        #     return BigQueryGenerator(metric=metric, dialect=dialect)
        # Add more database types as needed
        else:
            raise ValueError(f"Unsupported dialect: {source_type}")