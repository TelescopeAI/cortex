from typing import Optional, Dict, Any
import re

from cortex.core.query.engine.base import BaseQueryGenerator
from cortex.core.query.engine.processors.join_processor import JoinProcessor
from cortex.core.query.engine.processors.aggregation_processor import AggregationProcessor
from cortex.core.query.engine.processors.filter_processor import FilterProcessor
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.semantics.measure import SemanticMeasureType


class SQLQueryGenerator(BaseQueryGenerator):
    """Base implementation for SQL query generators with common functionality"""

    def generate_query(self, parameters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> str:
        """Generate a complete SQL query based on the metric with optional parameters and limit/offset"""
        # Use metric's default limit if no limit provided in execution request
        effective_limit = limit if limit is not None else self.metric.limit
        
        # If custom query is provided, substitute parameters and add limit if specified
        if self.metric.query:
            query = self._substitute_parameters(self.metric.query, parameters)
            limit_clause = self._build_limit_clause(effective_limit, offset)
            if limit_clause:
                query += f" {limit_clause}"
            return query

        # Otherwise, build the query from scratch
        select_clause = self._build_select_clause()
        from_clause = self._build_from_clause()
        join_clause = self._build_join_clause()
        where_clause = self._build_where_clause()
        group_by_clause = self._build_group_by_clause()
        having_clause = self._build_having_clause()
        order_by_clause = self._build_order_by_clause()
        limit_clause = self._build_limit_clause(effective_limit, offset)

        # Assemble the query with proper formatting
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
        if limit_clause:
            query_parts.append(limit_clause)

        assembled_query = self._format_query_with_line_breaks(query_parts)
        
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
                select_parts.append(self._format_dimension(dimension))
        
        # Add aggregations
        if self.metric.aggregations:
            aggregation_clause = AggregationProcessor.process_aggregations(self.metric.aggregations)
            if aggregation_clause:
                select_parts.append(aggregation_clause)
        
        if not select_parts:
            return "SELECT *"
        
        # Format SELECT clause with line breaks for multiple columns
        if len(select_parts) > 2:
            # For many columns, put each on a new line with indentation
            formatted_parts = [select_parts[0]]  # First column
            for part in select_parts[1:]:
                formatted_parts.append(f"\n  {part}")
            return f"SELECT {', '.join(formatted_parts)}"
        else:
            # For few columns, keep them on the same line
            return f"SELECT {', '.join(select_parts)}"

    def _get_qualified_column_name(self, column_query: str, table_name: Optional[str] = None) -> str:
        """Get a fully qualified column name with table prefix when joins are present"""
        # If no joins are present, return the column as-is
        if not self.metric.joins:
            return column_query
        
        # If column already contains a table prefix (has a dot), return as-is
        if '.' in column_query:
            return column_query
        
        # Use provided table name or default to metric's main table
        table_prefix = table_name or self.metric.table_name
        return f"{table_prefix}.{column_query}"

    def _format_measure(self, measure: SemanticMeasure) -> str:
        """Format a measure for the SELECT clause based on its type"""
        # Get the qualified column name (with table prefix if joins are present)
        qualified_query = self._get_qualified_column_name(measure.query, measure.table)
        
        if measure.type == SemanticMeasureType.COUNT:
            return f'COUNT({qualified_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.SUM:
            return f'SUM({qualified_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.AVG:
            return f'AVG({qualified_query}) AS "{measure.name}"'
        # Default case
        return f'{qualified_query} AS "{measure.name}"'

    def _format_dimension(self, dimension: SemanticDimension) -> str:
        """Format a dimension for the SELECT clause"""
        qualified_query = self._get_qualified_column_name(dimension.query, dimension.table)
        return f"{qualified_query} AS \"{dimension.name}\""

    def _build_from_clause(self) -> str:
        """Build the FROM clause based on metric's table"""
        return f"FROM\n  {self.metric.table_name}"

    def _build_where_clause(self) -> Optional[str]:
        """Build WHERE clause using FilterProcessor"""
        if not self.metric.filters:
            return None
        
        where_clause, _ = FilterProcessor.process_filters(
            self.metric.filters, 
            table_prefix=self.metric.table_name
        )
        
        if where_clause:
            return f"WHERE {where_clause}"
        return None

    def _build_group_by_clause(self) -> Optional[str]:
        """Build GROUP BY clause if dimensions are present"""
        if not self.metric.dimensions:
            return None

        # Use qualified column names when joins are present
        dimensions = [self._get_qualified_column_name(dim.query, dim.table) for dim in self.metric.dimensions]
        
        # Format GROUP BY with line breaks for multiple columns
        if len(dimensions) > 1:
            formatted_dimensions = [dimensions[0]]  # First dimension
            for dim in dimensions[1:]:
                formatted_dimensions.append(f"\n  {dim}")
            return f"GROUP BY {', '.join(formatted_dimensions)}"
        else:
            return f"GROUP BY {', '.join(dimensions)}"

    def _build_join_clause(self) -> Optional[str]:
        """Build JOIN clause using JoinProcessor"""
        if not self.metric.joins:
            return None
        
        return JoinProcessor.process_joins(self.metric.joins)

    def _build_having_clause(self) -> Optional[str]:
        """Build HAVING clause for aggregated conditions using FilterProcessor"""
        if not self.metric.filters:
            return None
        
        _, having_clause = FilterProcessor.process_filters(
            self.metric.filters, 
            table_prefix=self.metric.table_name
        )
        
        if having_clause:
            return f"HAVING {having_clause}"
        return None

    def _build_order_by_clause(self) -> Optional[str]:
        """Build ORDER BY clause with qualified column names when joins are present"""
        # This is a basic implementation - can be enhanced based on specific needs
        # When implementing ORDER BY, ensure to use self._get_qualified_column_name() for column references
        return None

    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build LIMIT clause for the query"""
        if limit is None and offset is None:
            return None
        
        if limit is not None and offset is not None:
            return f"LIMIT {limit} OFFSET {offset}"
        elif limit is not None:
            return f"LIMIT {limit}"
        elif offset is not None:
            return f"OFFSET {offset}"
        
        return None

    def _format_query_with_line_breaks(self, query_parts: list) -> str:
        """Format the query with appropriate line breaks and indentation"""
        if not query_parts:
            return ""
        
        formatted_parts = []
        
        # Always start with SELECT and FROM on separate lines
        if len(query_parts) >= 2:
            formatted_parts.append(query_parts[0])  # SELECT
            formatted_parts.append(f"\n{query_parts[1]}")  # FROM on new line
        
        # Add remaining clauses with proper line breaks
        for i, part in enumerate(query_parts[2:], start=2):
            if part:
                # Add line break for each clause (keywords are now included in the clause content)
                formatted_parts.append(f"\n{part}")
        
        return " ".join(formatted_parts)

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
