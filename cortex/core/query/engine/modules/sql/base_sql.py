from typing import Optional, Dict, Any, List
import re
from abc import abstractmethod

from cortex.core.query.engine.base import BaseQueryGenerator
from cortex.core.query.engine.processors.join_processor import JoinProcessor
from cortex.core.query.engine.processors.aggregation_processor import AggregationProcessor
from cortex.core.query.engine.processors.filter_processor import FilterProcessor
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.semantics.output_formats import FormattingMap
from cortex.core.types.time import TimeGrain


class SQLQueryGenerator(BaseQueryGenerator):
    """Base implementation for SQL query generators with common functionality"""

    # Optional binding that can redirect FROM and map logical names to physical columns
    binding: Optional[Any] = None

    def generate_query(self, parameters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None, grouped: Optional[bool] = None) -> str:
        """Generate a complete SQL query based on the metric with optional parameters and limit/offset"""
        # Use metric's default limit if no limit provided in execution request
        effective_limit = limit if limit is not None else self.metric.limit
        
        # Determine if grouping should be applied
        # If grouped parameter is explicitly set in request, use that
        # Otherwise, use the metric's default grouped setting
        effective_grouped = grouped if grouped is not None else (self.metric.grouped if self.metric.grouped is not None else True)
        
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
        group_by_clause = self._build_group_by_clause(effective_grouped)
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

        # Collect all formatting from semantic objects and store as instance variable
        self.formatting_map = OutputProcessor.collect_semantic_formatting(
            measures=self.metric.measures,
            dimensions=self.metric.dimensions,
            filters=self.metric.filters
        )

        # Add measures
        if self.metric.measures:
            for measure in self.metric.measures:
                select_parts.append(self._format_measure(measure, self.formatting_map))

        # Add dimensions
        if self.metric.dimensions:
            for dimension in self.metric.dimensions:
                select_parts.append(self._format_dimension(dimension, self.formatting_map))
        
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

    def _format_measure(self, measure: SemanticMeasure, formatting_map: FormattingMap) -> str:
        """Format a measure for the SELECT clause based on its type and formatting"""
        # If a binding is present and it maps this logical measure name,
        # select the bound column directly to avoid double-aggregation.
        if self.binding and self.binding.column_mapping.get(measure.name):
            bound_col = self.binding.column_mapping[measure.name]
            return f'{bound_col} AS "{measure.name}"'

        # Get the qualified column name (with table prefix if joins are present)
        qualified_query = self._get_qualified_column_name(measure.query, measure.table)

        # Apply any IN_QUERY formatting using database-specific implementation
        formatted_query = self._apply_database_formatting(qualified_query, measure.name, formatting_map)

        if measure.type == SemanticMeasureType.COUNT:
            return f'COUNT({formatted_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.SUM:
            return f'SUM({formatted_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.AVG:
            return f'AVG({formatted_query}) AS "{measure.name}"'
        # Default case
        return f'{formatted_query} AS "{measure.name}"'

    def _format_dimension(self, dimension: SemanticDimension, formatting_map: FormattingMap) -> str:
        """Format a dimension for the SELECT clause with formatting"""
        # If a binding is present and it maps this logical dimension name,
        # project the bound column directly to ensure we read from rollup definitions.
        if self.binding and self.binding.column_mapping.get(dimension.name):
            bound_col = self.binding.column_mapping[dimension.name]
            return f"{bound_col} AS \"{dimension.name}\""

        qualified_query = self._get_qualified_column_name(dimension.query, dimension.table)

        # Apply any IN_QUERY formatting using database-specific implementation
        formatted_query = self._apply_database_formatting(qualified_query, dimension.name, formatting_map)

        return f"{formatted_query} AS \"{dimension.name}\""

    def _can_re_aggregate(self, measure: SemanticMeasure) -> bool:
        """Check if a measure is re-aggregatable (additive)."""
        return measure.type in [SemanticMeasureType.SUM, SemanticMeasureType.COUNT]

    def _re_aggregate_measure(self, measure: SemanticMeasure, bound_column: str) -> str:
        """Re-aggregate a bound column for coarser grain requests."""
        if measure.type == SemanticMeasureType.SUM:
            return f'SUM({bound_column}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.COUNT:
            return f'SUM({bound_column}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.AVG:
            # For AVG, we need separate sum/count columns in the rollup
            sum_col = bound_column.replace("_avg", "_sum")
            count_col = bound_column.replace("_avg", "_count")
            return f'CASE WHEN SUM({count_col}) > 0 THEN SUM({sum_col}) / SUM({count_col}) ELSE NULL END AS "{measure.name}"'
        else:
            # Fallback: select the bound column directly
            return f'{bound_column} AS "{measure.name}"'

    def _needs_time_re_aggregation(self, requested_grain: Optional[TimeGrain]) -> bool:
        """Check if we need to re-aggregate time buckets for a coarser grain."""
        if not self.binding or not self.binding.rollup_grain or not requested_grain:
            return False
        
        grain_hierarchy = [TimeGrain.HOUR, TimeGrain.DAY, TimeGrain.WEEK, TimeGrain.MONTH, TimeGrain.QUARTER, TimeGrain.YEAR]
        try:
            rollup_idx = grain_hierarchy.index(self.binding.rollup_grain)
            requested_idx = grain_hierarchy.index(requested_grain)
            return requested_idx > rollup_idx  # Coarser grain requested
        except ValueError:
            return False

    def _get_table_prefix(self) -> str:
        """Get the appropriate table prefix/name for column qualification."""
        if self.binding and getattr(self.binding, 'qualified_table', None):
            # Extract table name from qualified table (remove quotes and schema)
            qualified_table = self.binding.qualified_table
            if '.' in qualified_table:
                # Handle "schema"."table" format
                return qualified_table.split('.')[-1].strip('"')
            else:
                # Handle "table" format
                return qualified_table.strip('"')
        return self.metric.table_name

    def _build_from_clause(self) -> str:
        """Build the FROM clause based on metric's table or binding."""
        if self.binding and getattr(self.binding, 'qualified_table', None):
            return f"FROM\n  {self.binding.qualified_table}"
        return f"FROM\n  {self.metric.table_name}"

    def _build_where_clause(self) -> Optional[str]:
        """Build WHERE clause using FilterProcessor"""
        if not self.metric.filters:
            return None
        
        where_clause, _ = FilterProcessor.process_filters(
            self.metric.filters, 
            table_prefix=self._get_table_prefix(),
            formatting_map=self.formatting_map
        )
        
        if where_clause:
            return f"WHERE {where_clause}"
        return None

    def _build_group_by_clause(self, grouped: bool) -> Optional[str]:
        """Build GROUP BY clause if dimensions are present and grouping is enabled"""
        if not self.metric.dimensions or not grouped:
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
            table_prefix=self._get_table_prefix(),
            formatting_map=self.formatting_map
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
        """Substitute $CORTEX_ parameters in the query string"""
        if not parameters:
            return query
        
        substituted_query = query
        
        # Replace $CORTEX_ parameter placeholders with actual values
        for param_name, param_value in parameters.items():
            # Only handle $CORTEX_ pattern to avoid double substitution
            pattern = f"$CORTEX_{param_name}"
            
            # Use str() for all values - let SQL formatters handle proper quoting
            substituted_query = substituted_query.replace(pattern, str(param_value))
        
        return substituted_query

    @abstractmethod
    def _apply_database_formatting(self, column_expression: str, object_name: str, formatting_map: FormattingMap) -> str:
        """Apply database-specific formatting to a column expression"""
        pass
