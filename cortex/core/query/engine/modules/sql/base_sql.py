from typing import Optional, Dict, Any
import re

from cortex.core.query.engine.base import BaseQueryGenerator
from cortex.core.query.engine.processors.join_processor import JoinProcessor
from cortex.core.query.engine.processors.aggregation_processor import AggregationProcessor
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.semantics.measure import SemanticMeasureType


class SQLQueryGenerator(BaseQueryGenerator):
    """Base implementation for SQL query generators with common functionality"""

    def generate_query(self, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Generate a complete SQL query based on the metric with optional parameters"""
        # If custom query is provided, substitute parameters and return
        if self.metric.query:
            return self._substitute_parameters(self.metric.query, parameters)

        # Otherwise, build the query from scratch
        select_clause = self._build_select_clause()
        from_clause = self._build_from_clause()
        join_clause = self._build_join_clause()
        where_clause = self._build_where_clause()
        group_by_clause = self._build_group_by_clause()
        having_clause = self._build_having_clause()
        order_by_clause = self._build_order_by_clause()

        # Assemble the query
        query_parts = [select_clause, from_clause]

        if join_clause:
            query_parts.append(join_clause)
        if where_clause:
            query_parts.append(where_clause)
        if group_by_clause:
            query_parts.append(group_by_clause)
        if having_clause:
            query_parts.append(having_clause)
        if order_by_clause:
            query_parts.append(order_by_clause)

        assembled_query = " ".join(query_parts)
        
        # Substitute parameters in the assembled query
        return self._substitute_parameters(assembled_query, parameters)

    def _extend_existing_query(self) -> str:
        """Extend an existing query with additional clauses"""
        # Implementation to extend a query provided in metric.query
        # This would likely involve parsing the existing query and adding to it
        pass

    def _build_select_clause(self) -> str:
        """Build the SELECT clause with measures, dimensions, and aggregations"""
        select_parts = []

        # Auto-detect SELECT * if no measures and dimensions
        if not self.metric.measures and not self.metric.dimensions and not self.metric.aggregations:
            return "SELECT *"

        # Add measures
        if self.metric.measures:
            for measure in self.metric.measures:
                select_parts.append(self._format_measure(measure))

        # Add dimensions
        if self.metric.dimensions:
            for dimension in self.metric.dimensions:
                select_parts.append(f"{dimension.query} AS \"{dimension.name}\"")
        
        # Add aggregations
        if self.metric.aggregations:
            aggregation_clause = AggregationProcessor.process_aggregations(self.metric.aggregations)
            if aggregation_clause:
                select_parts.append(aggregation_clause)
        
        if not select_parts:
            return "SELECT *"
        
        return f"SELECT {', '.join(select_parts)}"

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

    def _build_join_clause(self) -> Optional[str]:
        """Build JOIN clause using JoinProcessor"""
        if not self.metric.joins:
            return None
        
        return JoinProcessor.process_joins(self.metric.joins)

    def _build_having_clause(self) -> Optional[str]:
        """Build HAVING clause for aggregated conditions"""
        # This is a basic implementation - can be enhanced based on specific needs
        return None

    def _build_order_by_clause(self) -> Optional[str]:
        """Build ORDER BY clause"""
        # This is a basic implementation - can be enhanced based on specific needs
        return None

    def _substitute_parameters(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Substitute parameters in the query string"""
        if not parameters:
            return query
        
        substituted_query = query
        
        # Replace parameter placeholders with actual values
        for param_name, param_value in parameters.items():
            # Handle different parameter formats: {param}, :param, ${param}
            patterns = [
                f"{{{param_name}}}",      # {param_name}
                f":{param_name}",         # :param_name
                f"${{{param_name}}}"      # ${param_name}
            ]
            
            for pattern in patterns:
                if isinstance(param_value, str):
                    # Quote string values
                    substituted_query = substituted_query.replace(pattern, f"'{param_value}'")
                else:
                    # Use numeric/boolean values as-is
                    substituted_query = substituted_query.replace(pattern, str(param_value))
        
        return substituted_query
