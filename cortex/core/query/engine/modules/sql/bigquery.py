from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure

class BigQueryGenerator(SQLQueryGenerator):
    """BigQuery-specific query generator"""

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure with BigQuery-specific functions if needed"""
        # Override for BigQuery syntax
        if measure.type == "date_trunc":
            return f"TIMESTAMP_TRUNC({measure.query}, {measure.format}) AS {measure.name}"
        return super()._format_measure(measure)

    def _format_dimension(self, dimension: SemanticDimension) -> str:
        """Format a dimension with BigQuery-specific functions if needed"""
        # For now, use the base implementation
        return super()._format_dimension(dimension)

    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build LIMIT clause for BigQuery (supports LIMIT and OFFSET)"""
        if limit is None and offset is None:
            return None
        
        if limit is not None and offset is not None:
            return f"LIMIT {limit} OFFSET {offset}"
        elif limit is not None:
            return f"LIMIT {limit}"
        elif offset is not None:
            return f"OFFSET {offset}"
        
        return None