from typing import Optional, Dict, Any, List, Tuple

from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.types.time import TimeGrain
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.output_formats import OutputFormat, OutputFormatType, FormatType, OutputFormatMode, FormattingMap
from cortex.core.semantics.registry import SemanticRegistry


class SQLiteQueryGenerator(SQLQueryGenerator):
    """SQLite-specific query generator"""

    def _get_qualified_column_name(self, column_query: str, table_name: Optional[str] = None) -> str:
        """
        Get a fully qualified column name with proper SQLite quoting.
        Automatically uses the aliased table name if the table has been aliased in a JOIN.
        
        SQLite uses double quotes (") for identifiers to preserve case and handle special characters.
        This ensures all column references are properly quoted with double quotes.
        """
        def _quote_column(column: str) -> str:
            """Always quote column names for SQLite with double quotes unless already quoted"""
            column = column.strip()
            if column.startswith('"') and column.endswith('"'):
                return column
            return f'"{column}"'
        
        # Determine if joins are present
        has_joins = bool(self.metric.joins)
        
        # Check if this table has been aliased in a JOIN
        effective_table_name = table_name
        if table_name and self._table_alias_map and table_name in self._table_alias_map:
            effective_table_name = self._table_alias_map[table_name]
        
        # Get the table prefix to use
        table_prefix = effective_table_name or self.metric.table_name
        
        # If column already contains a table prefix (has a dot), handle it
        if '.' in column_query:
            parts = column_query.split('.', 1)
            table_part = parts[0].strip()
            column_part = parts[1].strip()
            
            # Always quote the column part, keep or replace the table prefix as needed
            if table_prefix and has_joins:
                # Use the provided table prefix (which may be an alias)
                return f"{table_prefix}.{_quote_column(column_part)}"
            else:
                # Keep existing table prefix but quote the column
                return f"{table_part}.{_quote_column(column_part)}"
        else:
            # Column doesn't have a table prefix - add one if there are joins
            if has_joins and table_prefix:
                return f"{table_prefix}.{_quote_column(column_query)}"
            elif table_prefix:
                # Even without joins, if we have a table name, qualify the column
                return f"{table_prefix}.{_quote_column(column_query)}"
            else:
                # No table information, just quote the column
                return _quote_column(column_query)

    def _format_measure(self, measure: SemanticMeasure, formatting_map: FormattingMap) -> str:
        """Format a measure with SQLite-specific syntax"""
        # If a binding is present and it maps this logical measure name,
        # select the bound column directly to avoid double-aggregation.
        if self.binding and self.binding.column_mapping.get(measure.name):
            bound_col = self.binding.column_mapping[measure.name]
            return f'{bound_col} AS "{measure.name}"'

        # Check if using conditional logic
        if measure.conditional and measure.conditions:
            # Use condition processor to generate CASE WHEN SQL
            from cortex.core.query.engine.processors.condition_processor import ConditionProcessor
            condition_sql = ConditionProcessor.process_condition(
                measure.conditions,
                self._table_alias_map,
                self.source_type.value
            )
            
            # Wrap in aggregation function
            from cortex.core.types.semantics.measure import SemanticMeasureType
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

        from cortex.core.types.semantics.measure import SemanticMeasureType
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
        """Format a dimension for the SELECT clause with SQLite-specific quoting"""
        # If a binding is present and it maps this logical dimension name,
        # project the bound column directly to ensure we read from rollup definitions.
        if self.binding and self.binding.column_mapping.get(dimension.name):
            bound_col = self.binding.column_mapping[dimension.name]
            return f"{bound_col} AS \"{dimension.name}\""

        # Check if using conditional logic
        if dimension.conditional and dimension.conditions:
            # Use condition processor to generate CASE WHEN SQL
            from cortex.core.query.engine.processors.condition_processor import ConditionProcessor
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
    
    def _build_group_by_clause(self, grouped: bool) -> Optional[str]:
        """
        Build GROUP BY clause for SQLite with quoted identifiers.
        Uses aliases from the SELECT clause to ensure consistency.
        """
        if not self.metric.dimensions or not grouped:
            return None

        # Use dimension aliases from SemanticRegistry
        dimension_aliases = SemanticRegistry.get_dimension_aliases(self.metric.dimensions)
        
        # Format GROUP BY with line breaks for multiple columns
        if len(dimension_aliases) > 1:
            formatted_dimensions = [dimension_aliases[0]]  # First dimension
            for dim in dimension_aliases[1:]:
                formatted_dimensions.append(f"\n  {dim}")
            return f"GROUP BY {', '.join(formatted_dimensions)}"
        else:
            return f"GROUP BY {', '.join(dimension_aliases)}"

    def _build_limit_clause(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Optional[str]:
        """Build LIMIT clause for SQLite (supports LIMIT and OFFSET)"""
        if limit is None and offset is None:
            return None
        
        if limit is not None and offset is not None:
            return f"LIMIT {limit} OFFSET {offset}"
        elif limit is not None:
            return f"LIMIT {limit}"
        elif offset is not None:
            return f"OFFSET {offset}"
        
        return None

    # SQLite does not support ROLLUP, so hierarchical grouping is not available
    def _supports_hierarchical_grouping(self) -> bool:
        return False

    def _apply_database_formatting(self, column_expression: str, object_name: str, formatting_map: FormattingMap) -> str:
        """Apply SQLite-specific formatting to a column expression"""
        if object_name not in formatting_map:
            return column_expression
        
        formats = formatting_map[object_name]
        if not formats:
            return column_expression
        
        # Apply formats in sequence, building up the SQL expression
        current_expression = column_expression
        
        for format_def in formats:
            if format_def.mode == OutputFormatMode.IN_QUERY:
                current_expression = self._apply_sqlite_format(current_expression, format_def)
            
        return current_expression
    
    def _apply_sqlite_format(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply a single SQLite format to a column expression"""
        if format_def.type == OutputFormatType.FORMAT:
            return self._apply_sqlite_string_format(column_expression, format_def)
        elif format_def.type == OutputFormatType.CAST:
            return self._apply_sqlite_cast(column_expression, format_def)
        elif format_def.type == OutputFormatType.CALCULATE:
            return self._apply_sqlite_calculate(column_expression, format_def)
        elif format_def.type == OutputFormatType.COMBINE:
            return self._apply_sqlite_combine(column_expression, format_def)
        else:
            return column_expression
    
    def _apply_sqlite_string_format(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply SQLite string formatting using strftime for dates/times"""
        if not format_def.format_string:
            return column_expression
        
        format_type = format_def.format_type or FormatType.DATETIME
        
        if format_type == FormatType.DATETIME:
            # Handle date/time formatting using strftime
            # Convert PostgreSQL format codes to SQLite format codes
            sqlite_format = self._convert_format_string_to_sqlite(format_def.format_string)
            return f"strftime('{sqlite_format}', {column_expression})"
                
        elif format_type == FormatType.NUMBER:
            # SQLite doesn't have a built-in number formatting function like MySQL's FORMAT
            # We can use CAST and string concatenation, but for now return as-is
            return column_expression
                
        elif format_type == FormatType.CURRENCY:
            # For currency, use || operator to concatenate with symbol
            return f"'$' || {column_expression}"
            
        elif format_type == FormatType.PERCENTAGE:
            # For percentage, multiply by 100 and concatenate with %
            return f"CAST({column_expression} * 100 AS TEXT) || '%'"
            
        elif format_type == FormatType.CUSTOM:
            # Handle custom format strings - try to infer the type
            format_upper = format_def.format_string.upper()
            if any(word in format_upper for word in ['%Y', '%M', '%D', '%H', '%I', '%S', '%W']):
                # Looks like a SQLite date/time format
                return f"strftime('{format_def.format_string}', {column_expression})"
            else:
                # Return as-is for other formats
                return column_expression
            
        else:
            # Fallback
            return column_expression
    
    def _convert_format_string_to_sqlite(self, postgres_format: str) -> str:
        """
        Convert PostgreSQL TO_CHAR format strings to SQLite strftime format strings.
        This is a basic conversion - more complex formats may need manual adjustment.
        """
        # Common PostgreSQL to SQLite format code mappings
        mappings = {
            'YYYY': '%Y',  # 4-digit year
            'YY': '%y',    # 2-digit year
            'MM': '%m',    # Month (01-12)
            'Mon': '%b',   # Abbreviated month name
            'Month': '%B',  # Full month name
            'DD': '%d',    # Day of month (01-31)
            'HH24': '%H',  # Hour (00-23)
            'HH12': '%I',  # Hour (01-12)
            'MI': '%M',   # Minutes (00-59)
            'SS': '%S',   # Seconds (00-59)
        }
        
        sqlite_format = postgres_format
        for pg_code, sqlite_code in mappings.items():
            sqlite_format = sqlite_format.replace(pg_code, sqlite_code)
        
        return sqlite_format
    
    def _apply_sqlite_cast(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply SQLite CAST formatting"""
        if not format_def.target_type:
            return column_expression
            
        # Map target types to SQLite CAST types
        sql_type_mapping = {
            "string": "TEXT",
            "integer": "INTEGER",
            "float": "REAL",
            "double": "REAL",
            "boolean": "INTEGER",  # SQLite uses 0/1 for boolean
            "date": "DATE",
            "timestamp": "DATETIME",
            "datetime": "DATETIME"
        }
        
        sql_type = sql_type_mapping.get(format_def.target_type, "TEXT")
        return f"CAST({column_expression} AS {sql_type})"
    
    def _apply_sqlite_calculate(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply SQLite calculation formatting"""
        if not format_def.operands or not format_def.operation:
            return column_expression
            
        # For IN_QUERY calculations, we need to build the actual SQL expression
        # The operands should be column names or literal values
        if not format_def.operands:
            return column_expression
            
        # Start with the base column
        result = column_expression
        
        # Apply operations to operands
        for operand in format_def.operands:
            # Handle numeric literals vs column names
            if operand.isdigit() or (operand.startswith('-') and operand[1:].isdigit()):
                # Numeric literal - use as-is
                operand_value = operand
            else:
                # Column name - qualify it if needed
                operand_value = operand
            
            if format_def.operation == "add":
                result = f"({result} + {operand_value})"
            elif format_def.operation == "subtract":
                result = f"({result} - {operand_value})"
            elif format_def.operation == "multiply":
                result = f"({result} * {operand_value})"
            elif format_def.operation == "divide":
                result = f"({result} / {operand_value})"
            else:
                # Unknown operation, return original
                return column_expression
        
        return result
    
    def _apply_sqlite_combine(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply SQLite combine formatting using || operator"""
        if not format_def.source_columns:
            return column_expression
            
        # Build || (concatenation) expression for combining columns
        delimiter = format_def.delimiter or " "
        
        # Start with the base column
        concat_parts = [column_expression]
        
        # Add other source columns
        for col in format_def.source_columns:
            concat_parts.append(f"'{delimiter}'")
            concat_parts.append(col)
            
        return f" || ".join(concat_parts)
    
    def _build_combine_expression(self, parts: List[Tuple[str, Optional[str]]]) -> str:
        """
        Build SQLite || expression for combining multiple columns.
        
        Args:
            parts: List of (column_expression, delimiter_before_column) tuples
                   First tuple has None as delimiter
                   
        Returns:
            SQLite || concatenation expression
            
        Example:
            parts = [("first_name", None), ("last_name", " ")]
            returns: first_name || ' ' || last_name
        """
        if len(parts) == 1:
            return parts[0][0]
        
        concat_parts = []
        for col, delimiter in parts:
            if delimiter is not None:
                # Add delimiter literal before the column
                concat_parts.append(f"'{delimiter}'")
            concat_parts.append(col)
        
        return f" || ".join(concat_parts)
