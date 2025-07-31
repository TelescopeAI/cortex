from typing import Optional

from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure


class PostgresQueryGenerator(SQLQueryGenerator):
    """PostgreSQL-specific query generator"""

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure with PostgreSQL-specific functions if needed"""
        # Override parent method for PostgreSQL-specific syntax
        if measure.type == "date_trunc":
            return f"DATE_TRUNC('{measure.format}', {measure.query}) AS {measure.name}"
        return super()._format_measure(measure)

    def _format_dimension(self, dimension: SemanticDimension) -> str:
        """Format a dimension with PostgreSQL-specific functions if needed"""
        # For now, use the base implementation
        return super()._format_dimension(dimension)

    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build LIMIT clause for PostgreSQL (supports LIMIT and OFFSET)"""
        if limit is None and offset is None:
            return None
        
        if limit is not None and offset is not None:
            return f"LIMIT {limit} OFFSET {offset}"
        elif limit is not None:
            return f"LIMIT {limit}"
        elif offset is not None:
            return f"OFFSET {offset}"
        
        return None
