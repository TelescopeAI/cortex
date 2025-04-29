from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.semantics.measures import SemanticMeasure


class PostgresQueryGenerator(SQLQueryGenerator):
    """PostgreSQL-specific query generator"""

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure with PostgreSQL-specific functions if needed"""
        # Override parent method for PostgreSQL-specific syntax
        if measure.type == "date_trunc":
            return f"DATE_TRUNC('{measure.format}', {measure.query}) AS {measure.name}"
        return super()._format_measure(measure)


class BigQueryGenerator(SQLQueryGenerator):
    """BigQuery-specific query generator"""

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure with BigQuery-specific functions if needed"""
        # Override for BigQuery syntax
        if measure.type == "date_trunc":
            return f"TIMESTAMP_TRUNC({measure.query}, {measure.format}) AS {measure.name}"
        return super()._format_measure(measure)