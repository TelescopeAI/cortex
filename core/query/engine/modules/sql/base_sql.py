from typing import Optional

from core.query.engine.base import BaseQueryGenerator
from core.semantics.measures import SemanticMeasure
from core.types.semantics.measure import SemanticMeasureType


class SQLQueryGenerator(BaseQueryGenerator):
    """Base implementation for SQL query generators with common functionality"""

    def generate_query(self) -> str:
        """Generate a complete SQL query based on the metric"""
        # If query is provided in the metric, use it as a base
        if self.metric.query:
            return self._extend_existing_query()

        # Otherwise, build the query from scratch
        select_clause = self._build_select_clause()
        from_clause = self._build_from_clause()
        where_clause = self._build_where_clause()
        group_by_clause = self._build_group_by_clause()

        query = f"{select_clause} {from_clause}"

        if where_clause:
            query += f" {where_clause}"

        if group_by_clause:
            query += f" {group_by_clause}"
        return query

    def _extend_existing_query(self) -> str:
        """Extend an existing query with additional clauses"""
        # Implementation to extend a query provided in metric.query
        # This would likely involve parsing the existing query and adding to it
        pass

    def _build_select_clause(self) -> str:
        """Build the SELECT clause with measures"""
        query = "SELECT "
        measures = self.metric.measures

        if not measures:
            return "SELECT *"

        measure_queries = []
        for measure in measures:
            measure_queries.append(self._format_measure(measure))

        query += ", ".join(measure_queries)
        return query

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure for the SELECT clause based on its type"""
        if measure.type is SemanticMeasureType.COUNT:
            return f"COUNT({measure.query}) AS \"{measure.name}\""
        elif measure.type is SemanticMeasureType.SUM:
            return f"SUM({measure.query}) AS \"{measure.name}\""
        elif measure.type is SemanticMeasureType.AVG:
            return f"AVG({measure.query}) AS \"{measure.name}\""
        # Default case
        return f"{measure.query} AS \"{measure.name}\""

    def _build_from_clause(self) -> str:
        """Build the FROM clause based on metric's table"""
        return f"FROM {self.metric.table}"

    def _build_where_clause(self) -> Optional[str]:
        """Build WHERE clause - default implementation returns None"""
        return None

    def _build_group_by_clause(self) -> Optional[str]:
        """Build GROUP BY clause if dimensions are present"""
        if not self.metric.dimensions:
            return None

        dimensions = [dim.query for dim in self.metric.dimensions]
        return f"GROUP BY {', '.join(dimensions)}"
