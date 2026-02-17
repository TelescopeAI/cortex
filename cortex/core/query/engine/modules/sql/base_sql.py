from typing import Optional, Dict, Any, List, Tuple
import re
from abc import abstractmethod

from cortex.core.query.engine.base import BaseQueryGenerator
from cortex.core.query.engine.processors.join_processor import JoinProcessor
from cortex.core.query.engine.processors.aggregation_processor import AggregationProcessor
from cortex.core.query.engine.processors.filter_processor import FilterProcessor
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.query.engine.processors.condition_processor import ConditionProcessor
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.registry import SemanticRegistry
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.semantics.output_formats import FormattingMap
from cortex.core.types.time import TimeGrain
from cortex.core.query.engine.processors.order_processor import OrderProcessor
from cortex.core.utils.schema_inference import get_qualified_column_name


class SQLQueryGenerator(BaseQueryGenerator):
    """Base implementation for SQL query generators with common functionality"""

    # Optional binding that can redirect FROM and map logical names to physical columns
    binding: Optional[Any] = None
    
    # Internal state: table alias mapping from original table names to their aliases in JOINs
    _table_alias_map: Optional[Dict[str, str]] = None

    def generate_query(self, parameters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None, offset: Optional[int] = None, grouped: Optional[bool] = None) -> str:
        """Generate a complete SQL query based on the metric with optional parameters and limit/offset"""
        # Use metric's default limit if no limit provided in execution request
        effective_limit = limit if limit is not None else self.metric.limit

        # Determine if grouping should be applied
        # If grouped parameter is explicitly set in request, use that
        # Otherwise, use the metric's default grouped setting
        effective_grouped = grouped if grouped is not None else (self.metric.grouped if self.metric.grouped is not None else True)

        # Determine if ordering should be applied
        # Use the metric's default ordered setting (defaults to True if not specified)
        effective_ordered = self.metric.ordered if self.metric.ordered is not None else True

        # If custom query is provided, substitute parameters and add limit if specified
        if self.metric.query:
            query = self._substitute_parameters(self.metric.query, parameters)
            limit_clause = self._build_limit_clause(effective_limit, offset)
            if limit_clause:
                query += f" {limit_clause}"
            return query

        # Check if this is a CTE query (multi-source composition)
        if self.metric.composition is not None and len(self.metric.composition) > 0:
            # Build CTE query
            query = self._build_cte_query(effective_grouped, effective_limit, offset)
            return self._substitute_parameters(query, parameters)

        # Otherwise, build the query from scratch
        # IMPORTANT: Build join clause first to populate table alias mappings
        join_clause = self._build_join_clause()

        # Now build SELECT clause with knowledge of table aliases
        select_clause = self._build_select_clause()
        from_clause = self._build_from_clause()
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

        # Add derivations (window functions and arithmetic)
        if self.metric.derivations:
            for derivation in self.metric.derivations:
                derivation_sql = self._format_derivation(derivation)
                if derivation_sql:
                    select_parts.append(derivation_sql)

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
        """
        Get a fully qualified column name with table prefix when joins are present.
        Automatically uses the aliased table name if the table has been aliased in a JOIN.
        """
        has_joins = bool(self.metric.joins)
        
        # Check if this table has been aliased in a JOIN
        effective_table_name = table_name
        if table_name and self._table_alias_map and table_name in self._table_alias_map:
            effective_table_name = self._table_alias_map[table_name]
        
        table_prefix = effective_table_name or self.metric.table_name
        return get_qualified_column_name(
            column_query=column_query,
            table_name=table_name,
            table_prefix=table_prefix,
            has_joins=has_joins
        )

    def _format_measure(self, measure: SemanticMeasure, formatting_map: FormattingMap) -> str:
        """Format a measure for the SELECT clause based on its type and formatting"""
        # If a binding is present and it maps this logical measure name,
        # select the bound column directly to avoid double-aggregation.
        if self.binding and self.binding.column_mapping.get(measure.name):
            bound_col = self.binding.column_mapping[measure.name]
            return f'{bound_col} AS "{measure.name}"'

        # Check if using conditional logic
        if measure.conditional and measure.conditions:
            # Use condition processor to generate CASE WHEN SQL
            condition_sql = ConditionProcessor.process_condition(
                measure.conditions,
                self._table_alias_map,
                self.source_type.value
            )
            
            # Wrap in aggregation function
            if measure.type == SemanticMeasureType.COUNT:
                agg_sql = f'COUNT({condition_sql})'
            elif measure.type == SemanticMeasureType.SUM:
                agg_sql = f'SUM({condition_sql})'
            elif measure.type == SemanticMeasureType.AVG:
                agg_sql = f'AVG({condition_sql})'
            elif measure.type == SemanticMeasureType.MIN:
                agg_sql = f'MIN({condition_sql})'
            elif measure.type == SemanticMeasureType.MAX:
                agg_sql = f'MAX({condition_sql})'
            elif measure.type == SemanticMeasureType.COUNT_DISTINCT:
                agg_sql = f'COUNT(DISTINCT {condition_sql})'
            else:
                agg_sql = condition_sql
            
            # Apply formatting if specified
            formatted_sql = self._apply_database_formatting(agg_sql, measure.name, formatting_map)
            
            return f'{formatted_sql} AS "{measure.name}"'
        
        # Standard simple query mode
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
        elif measure.type == SemanticMeasureType.MIN:
            return f'MIN({formatted_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.MAX:
            return f'MAX({formatted_query}) AS "{measure.name}"'
        elif measure.type == SemanticMeasureType.COUNT_DISTINCT:
            return f'COUNT(DISTINCT {formatted_query}) AS "{measure.name}"'
        # Default case
        return f'{formatted_query} AS "{measure.name}"'

    def _format_dimension(self, dimension: SemanticDimension, formatting_map: FormattingMap) -> str:
        """Format a dimension for the SELECT clause with formatting and column combination"""
        # If a binding is present and it maps this logical dimension name,
        # project the bound column directly to ensure we read from rollup definitions.
        if self.binding and self.binding.column_mapping.get(dimension.name):
            bound_col = self.binding.column_mapping[dimension.name]
            return f"{bound_col} AS \"{dimension.name}\""

        # Check if using conditional logic
        if dimension.conditional and dimension.conditions:
            # Use condition processor to generate CASE WHEN SQL
            condition_sql = ConditionProcessor.process_condition(
                dimension.conditions,
                self._table_alias_map,
                self.source_type.value
            )
            
            # Apply formatting if specified
            formatted_sql = self._apply_database_formatting(condition_sql, dimension.name, formatting_map)
            
            return f'{formatted_sql} AS "{dimension.name}"'

        # Check if we need to combine multiple columns
        if dimension.combine and len(dimension.combine) > 0:
            # Build list of (column_expression, delimiter_before_column) tuples
            # First column has no delimiter (None)
            parts = [(self._get_qualified_column_name(dimension.query, dimension.table), None)]
            
            # Add each combine column with its delimiter
            for combine_spec in dimension.combine:
                qualified_col = self._get_qualified_column_name(combine_spec.query, combine_spec.table)
                delimiter = combine_spec.delimiter if combine_spec.delimiter is not None else " "
                parts.append((qualified_col, delimiter))
            
            # Build the combined expression using database-specific implementation
            combined_expr = self._build_combine_expression(parts)
            
            # Apply any formatting on top of the combined expression
            formatted_expr = self._apply_database_formatting(combined_expr, dimension.name, formatting_map)
            
            return f"{formatted_expr} AS \"{dimension.name}\""
        else:
            # Standard single-column dimension
            qualified_query = self._get_qualified_column_name(dimension.query, dimension.table)

            # Apply any IN_QUERY formatting using database-specific implementation
            formatted_query = self._apply_database_formatting(qualified_query, dimension.name, formatting_map)

            return f"{formatted_query} AS \"{dimension.name}\""

    def _format_derivation(self, derivation) -> str:
        """
        Format a derivation (window function or arithmetic operation) for the SELECT clause.

        Args:
            derivation: DerivedEntity from cortex.core.semantics.derivations

        Returns:
            SQL string for the derivation
        """
        from cortex.core.semantics.derivations import DerivedEntityType

        deriv_type = derivation.type
        source_measure = derivation.source.measure
        deriv_name = derivation.name

        # Handle cross-CTE references (alias.measure)
        if "." in source_measure:
            # Cross-CTE reference - use as-is
            measure_ref = f'"{source_measure.split(".")[0]}"."{source_measure.split(".")[1]}"'
        else:
            # Local measure reference
            measure_ref = f'"{source_measure}"'

        # Cortex aggregate-as-window derivations
        if deriv_type == DerivedEntityType.PERCENT_OF_TOTAL:
            return f'{measure_ref} * 100.0 / SUM({measure_ref}) OVER () AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.RUNNING_TOTAL:
            order_dim = derivation.order_dimension
            return f'SUM({measure_ref}) OVER (ORDER BY "{order_dim}" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.CUMULATIVE_COUNT:
            order_dim = derivation.order_dimension
            return f'COUNT({measure_ref}) OVER (ORDER BY "{order_dim}" ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.SHARE:
            partition_dim = derivation.partition_by
            return f'{measure_ref} * 100.0 / SUM({measure_ref}) OVER (PARTITION BY "{partition_dim}") AS "{deriv_name}"'

        # Arithmetic derivations (two-input operations)
        elif deriv_type == DerivedEntityType.DIVIDE:
            by_measure = derivation.source.by
            if "." in by_measure:
                by_ref = f'"{by_measure.split(".")[0]}"."{by_measure.split(".")[1]}"'
            else:
                by_ref = f'"{by_measure}"'
            return f'CASE WHEN {by_ref} = 0 THEN NULL ELSE {measure_ref} * 1.0 / {by_ref} END AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.MULTIPLY:
            by_measure = derivation.source.by
            if "." in by_measure:
                by_ref = f'"{by_measure.split(".")[0]}"."{by_measure.split(".")[1]}"'
            else:
                by_ref = f'"{by_measure}"'
            return f'{measure_ref} * {by_ref} AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.SUBTRACT:
            by_measure = derivation.source.by
            if "." in by_measure:
                by_ref = f'"{by_measure.split(".")[0]}"."{by_measure.split(".")[1]}"'
            else:
                by_ref = f'"{by_measure}"'
            return f'{measure_ref} - {by_ref} AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.ADD:
            by_measure = derivation.source.by
            if "." in by_measure:
                by_ref = f'"{by_measure.split(".")[0]}"."{by_measure.split(".")[1]}"'
            else:
                by_ref = f'"{by_measure}"'
            return f'{measure_ref} + {by_ref} AS "{deriv_name}"'

        # PostgreSQL window functions - ranking
        elif deriv_type == DerivedEntityType.ROW_NUMBER:
            order_dim = derivation.order_dimension
            return f'ROW_NUMBER() OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.RANK:
            order_dim = derivation.order_dimension
            return f'RANK() OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.DENSE_RANK:
            order_dim = derivation.order_dimension
            return f'DENSE_RANK() OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.PERCENT_RANK:
            order_dim = derivation.order_dimension
            return f'PERCENT_RANK() OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.CUME_DIST:
            order_dim = derivation.order_dimension
            return f'CUME_DIST() OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.NTILE:
            order_dim = derivation.order_dimension
            n = derivation.n
            return f'NTILE({n}) OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        # PostgreSQL window functions - offset
        elif deriv_type == DerivedEntityType.LAG:
            order_dim = derivation.order_dimension
            offset = derivation.offset or 1
            default = derivation.default_value if derivation.default_value is not None else "NULL"
            return f'LAG({measure_ref}, {offset}, {default}) OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.LEAD:
            order_dim = derivation.order_dimension
            offset = derivation.offset or 1
            default = derivation.default_value if derivation.default_value is not None else "NULL"
            return f'LEAD({measure_ref}, {offset}, {default}) OVER (ORDER BY "{order_dim}") AS "{deriv_name}"'

        # PostgreSQL window functions - value
        elif deriv_type == DerivedEntityType.FIRST_VALUE:
            order_dim = derivation.order_dimension
            return f'FIRST_VALUE({measure_ref}) OVER (ORDER BY "{order_dim}" ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.LAST_VALUE:
            order_dim = derivation.order_dimension
            return f'LAST_VALUE({measure_ref}) OVER (ORDER BY "{order_dim}" ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS "{deriv_name}"'

        elif deriv_type == DerivedEntityType.NTH_VALUE:
            order_dim = derivation.order_dimension
            n = derivation.n
            return f'NTH_VALUE({measure_ref}, {n}) OVER (ORDER BY "{order_dim}" ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS "{deriv_name}"'

        else:
            # Unknown derivation type - return as-is
            return f'{measure_ref} AS "{deriv_name}"'

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
        """
        Build GROUP BY clause if dimensions are present and grouping is enabled.
        Uses aliases from the SELECT clause to ensure consistency and avoid issues
        with quoted identifiers and complex expressions.
        """
        if not self.metric.dimensions or not grouped:
            return None

        # Use dimension aliases (e.g., "Date", "Customer Name") instead of fully qualified names
        # This ensures consistency with the SELECT clause and works better with databases
        dimension_aliases = SemanticRegistry.get_dimension_aliases(self.metric.dimensions)
        
        # Format GROUP BY with line breaks for multiple columns
        if len(dimension_aliases) > 1:
            formatted_dimensions = [dimension_aliases[0]]  # First dimension
            for dim in dimension_aliases[1:]:
                formatted_dimensions.append(f"\n  {dim}")
            return f"GROUP BY {', '.join(formatted_dimensions)}"
        else:
            return f"GROUP BY {', '.join(dimension_aliases)}"

    def _build_join_clause(self) -> Optional[str]:
        """
        Build JOIN clause using JoinProcessor.
        Also builds and stores table alias mappings for use in SELECT and other clauses.
        """
        if not self.metric.joins:
            self._table_alias_map = {}
            return None
        
        # Pass the base table name to detect collisions with the FROM clause
        base_table = self.metric.table_name
        
        # Build the table alias mapping before generating the join clause
        self._table_alias_map = JoinProcessor.build_table_alias_map(self.metric.joins, base_table)
        
        return JoinProcessor.process_joins(self.metric.joins, base_table)

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
        """Build ORDER BY clause with context-aware semantic resolution"""
        # Get table prefix/name for qualified column names
        table_prefix = self._get_primary_table_name()
        
        # Determine if this is a grouped query
        is_grouped_query = self.metric.grouped and self.metric.dimensions
        
        # Build SELECT expressions mapping for semantic resolution
        select_expressions = self._build_select_expressions_map()
        
        return OrderProcessor.process_order_sequences(
            order_sequences=self.metric.order,
            measures=self.metric.measures,
            dimensions=self.metric.dimensions,
            table_prefix=table_prefix,
            formatting_map=getattr(self, 'formatting_map', None),
            apply_default_ordering=self.metric.ordered if self.metric.ordered is not None else True,
            is_grouped_query=is_grouped_query,
            select_expressions=select_expressions
        )
    
    def _build_select_expressions_map(self) -> Dict[str, str]:
        """Build a mapping of column aliases to their actual SELECT expressions"""
        expressions = {}
        
        # Add measure expressions
        if self.metric.measures:
            formatting_map = getattr(self, 'formatting_map', None)
            for measure in self.metric.measures:
                # Build the expression using the same logic as _format_measure
                formatted_expression = self._format_measure(measure, formatting_map or {})
                # Extract just the expression part (before AS "alias")
                if ' AS "' in formatted_expression:
                    expression = formatted_expression.split(' AS "')[0]
                    expressions[measure.name] = expression
                else:
                    expressions[measure.name] = formatted_expression
        
        # Add dimension expressions
        if self.metric.dimensions:
            formatting_map = getattr(self, 'formatting_map', None)
            for dimension in self.metric.dimensions:
                # Build the expression using the same logic as _format_dimension  
                formatted_expression = self._format_dimension(dimension, formatting_map or {})
                # Extract just the expression part (before AS "alias")
                if ' AS "' in formatted_expression:
                    expression = formatted_expression.split(' AS "')[0]
                    expressions[dimension.name] = expression
                else:
                    expressions[dimension.name] = formatted_expression
        
        return expressions
    
    def _get_primary_table_name(self) -> Optional[str]:
        """Get the primary table name for column qualification"""
        # Use the metric's table_name if available
        if self.metric.table_name:
            return self.metric.table_name
        
        # Extract from first measure or dimension if available
        if self.metric.measures and self.metric.measures[0].table:
            return self.metric.measures[0].table
        
        if self.metric.dimensions and self.metric.dimensions[0].table:
            return self.metric.dimensions[0].table
            
        return None

    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build LIMIT clause for the query, validating parameters to avoid SQL injection"""
        # Only allow integer values for limit and offset, else skip or raise
        clause_parts = []

        parsed_limit = None
        parsed_offset = None
        try:
            if limit is not None:
                parsed_limit = int(limit)
                if parsed_limit < 0:
                    raise ValueError("limit must be non-negative")
            if offset is not None:
                parsed_offset = int(offset)
                if parsed_offset < 0:
                    raise ValueError("offset must be non-negative")
        except (ValueError, TypeError):
            # If not valid integers, ignore and do not add clause
            return None

        if parsed_limit is not None and parsed_offset is not None:
            clause_parts.append(f"LIMIT {parsed_limit} OFFSET {parsed_offset}")
        elif parsed_limit is not None:
            clause_parts.append(f"LIMIT {parsed_limit}")
        elif parsed_offset is not None:
            clause_parts.append(f"OFFSET {parsed_offset}")

        return " ".join(clause_parts) if clause_parts else None

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

    def _build_cte_query(self, grouped: bool, limit: Optional[int], offset: Optional[int]) -> str:
        """
        Build a CTE (Common Table Expression) query for multi-source composition.

        Args:
            grouped: Whether to apply GROUP BY
            limit: Optional result limit
            offset: Optional result offset

        Returns:
            Complete CTE query string
        """
        cte_parts = []

        # Build primary CTE from the main metric
        primary_alias = self.metric.alias or "primary"
        primary_cte = self._build_cte_clause(self.metric, primary_alias, grouped)
        cte_parts.append(f'"{primary_alias}" AS (\n{primary_cte}\n)')

        # Build CTEs for each composition source
        for comp_source in self.metric.composition:
            comp_alias = comp_source.alias
            comp_cte = self._build_cte_clause(comp_source.metric, comp_alias, grouped)
            cte_parts.append(f'"{comp_alias}" AS (\n{comp_cte}\n)')

        # Build the outer SELECT
        outer_select = self._build_outer_select(primary_alias, self.metric.composition, self.metric.derivations)

        # Build the FROM + JOIN clause
        from_join = self._build_cte_join(primary_alias, self.metric.composition)

        # Build limit clause if needed
        limit_clause = self._build_limit_clause(limit, offset)

        # Assemble the complete CTE query
        cte_clause = f"WITH {',\n'.join(cte_parts)}"
        query_parts = [cte_clause, outer_select, from_join]
        if limit_clause:
            query_parts.append(limit_clause)

        return "\n".join(query_parts)

    def _build_cte_clause(self, metric, alias: str, grouped: bool) -> str:
        """
        Build the inner SELECT for a single CTE.

        Args:
            metric: SemanticMetric to generate CTE for
            alias: Alias for this CTE
            grouped: Whether to apply GROUP BY

        Returns:
            SQL string for the CTE inner query
        """
        select_parts = []

        # Add measures
        if metric.measures:
            for measure in metric.measures:
                select_parts.append(self._format_measure(measure, self.formatting_map))

        # Add dimensions
        if metric.dimensions:
            for dimension in metric.dimensions:
                select_parts.append(self._format_dimension(dimension, self.formatting_map))

        # Build SELECT
        select_clause = f"  SELECT {', '.join(select_parts)}"

        # Build FROM
        from_clause = f"  FROM \"{metric.table_name}\""

        # Build WHERE if filters present
        where_clause = None
        if metric.filters:
            where_conditions, _ = FilterProcessor.process_filters(
                metric.filters,
                table_prefix=metric.table_name,
                formatting_map=self.formatting_map
            )
            if where_conditions:
                where_clause = f"  WHERE {where_conditions}"

        # Build GROUP BY if needed
        group_by_clause = None
        if grouped and metric.dimensions:
            dimension_names = [f'"{d.name}"' for d in metric.dimensions]
            group_by_clause = f"  GROUP BY {', '.join(dimension_names)}"

        # Assemble CTE query
        parts = [select_clause, from_clause]
        if where_clause:
            parts.append(where_clause)
        if group_by_clause:
            parts.append(group_by_clause)

        return "\n".join(parts)

    def _build_outer_select(self, primary_alias: str, composition: List, derivations: Optional[List]) -> str:
        """
        Build the outer SELECT clause for a CTE query.

        Args:
            primary_alias: Alias of the primary CTE
            composition: List of CompositionSource objects
            derivations: Optional list of DerivedEntity objects

        Returns:
            SQL string for outer SELECT
        """
        select_parts = []

        # Select all measures/dimensions from primary CTE
        if self.metric.measures:
            for measure in self.metric.measures:
                select_parts.append(f'"{primary_alias}"."{measure.name}"')

        if self.metric.dimensions:
            for dimension in self.metric.dimensions:
                select_parts.append(f'"{primary_alias}"."{dimension.name}"')

        # Select measures from composed CTEs
        for comp_source in composition:
            comp_alias = comp_source.alias
            if comp_source.metric.measures:
                for measure in comp_source.metric.measures:
                    select_parts.append(f'"{comp_alias}"."{measure.name}"')

        # Add derivations (including cross-CTE derivations)
        if derivations:
            for derivation in derivations:
                derivation_sql = self._format_derivation(derivation)
                if derivation_sql:
                    # Extract just the expression part (remove the " AS name" suffix)
                    # derivation_sql is already formatted like: 'expr AS "name"'
                    select_parts.append(derivation_sql.split(' AS ')[0] + f' AS "{derivation.name}"')

        return f"SELECT {', '.join(select_parts)}"

    def _build_cte_join(self, primary_alias: str, composition: List) -> str:
        """
        Build the FROM + JOIN clause for a CTE query.

        Args:
            primary_alias: Alias of the primary CTE
            composition: List of CompositionSource objects

        Returns:
            SQL string for FROM + JOIN
        """
        from_clause = f'FROM "{primary_alias}"'

        join_clauses = []
        for comp_source in composition:
            comp_alias = comp_source.alias
            join_on_dims = comp_source.join_on

            # Build JOIN ON condition
            on_conditions = []
            for dim_name in join_on_dims:
                on_conditions.append(f'"{primary_alias}"."{dim_name}" = "{comp_alias}"."{dim_name}"')

            join_on = " AND ".join(on_conditions)
            join_clauses.append(f'INNER JOIN "{comp_alias}" ON {join_on}')

        if join_clauses:
            return from_clause + "\n" + "\n".join(join_clauses)
        else:
            return from_clause

    @abstractmethod
    def _apply_database_formatting(self, column_expression: str, object_name: str, formatting_map: FormattingMap) -> str:
        """Apply database-specific formatting to a column expression"""
        pass
    
    @abstractmethod
    def _build_combine_expression(self, parts: List[Tuple[str, Optional[str]]]) -> str:
        """
        Build a database-specific expression for combining multiple columns.
        
        Args:
            parts: List of (column_expression, delimiter_before_column) tuples
                   First column has delimiter=None, subsequent columns have their delimiter
        
        Returns:
            SQL expression that concatenates the columns with delimiters
        """
        pass
