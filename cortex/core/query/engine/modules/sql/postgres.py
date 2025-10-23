from typing import Optional, Dict, Any, List, Tuple

from cortex.core.query.engine.modules.sql.base_sql import SQLQueryGenerator
from cortex.core.types.time import TimeGrain
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.output_formats import OutputFormat, OutputFormatType, FormatType, OutputFormatMode, FormattingMap


class PostgresQueryGenerator(SQLQueryGenerator):
    """PostgreSQL-specific query generator"""

    def _get_qualified_column_name(self, column_query: str, table_name: Optional[str] = None) -> str:
        """
        Get a fully qualified column name with proper PostgreSQL quoting.
        Automatically uses the aliased table name if the table has been aliased in a JOIN.
        
        PostgreSQL requires column names to be quoted to preserve case and handle special characters.
        This ensures all column references are properly quoted.
        """
        def _quote_column(column: str) -> str:
            """Always quote column names for PostgreSQL unless already quoted"""
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

    def _format_measure(self, measure: SemanticMeasure, formatting_map: dict) -> str:
        """Format a measure with PostgreSQL-specific functions if needed"""
        # Override parent method for PostgreSQL-specific syntax
        if measure.type == "date_trunc":
            return f"DATE_TRUNC('{measure.format}', {measure.query}) AS {measure.name}"
        return super()._format_measure(measure, formatting_map)

    def _format_dimension(self, dimension: SemanticDimension, formatting_map: dict) -> str:
        """Format a dimension with PostgreSQL-specific functions if needed"""
        # For now, use the base implementation
        return super()._format_dimension(dimension, formatting_map)

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

    # Hierarchical grouping support (ROLLUP)
    def _supports_hierarchical_grouping(self) -> bool:
        return True

    def _group_by_hierarchical(self, dim_cols_sql: list[str]) -> str:
        inner = ", ".join(dim_cols_sql)
        return f"GROUP BY ROLLUP ({inner})"

    def _apply_database_formatting(self, column_expression: str, object_name: str, formatting_map: FormattingMap) -> str:
        """Apply PostgreSQL-specific formatting to a column expression"""
        if object_name not in formatting_map:
            return column_expression
        
        formats = formatting_map[object_name]
        if not formats:
            return column_expression
        
        # Apply formats in sequence, building up the SQL expression
        current_expression = column_expression
        
        for format_def in formats:
            if format_def.mode == OutputFormatMode.IN_QUERY:
                current_expression = self._apply_postgres_format(current_expression, format_def)
            
        return current_expression
    
    def _apply_postgres_format(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply a single PostgreSQL format to a column expression"""
        if format_def.type == OutputFormatType.FORMAT:
            return self._apply_postgres_string_format(column_expression, format_def)
        elif format_def.type == OutputFormatType.CAST:
            return self._apply_postgres_cast(column_expression, format_def)
        elif format_def.type == OutputFormatType.CALCULATE:
            return self._apply_postgres_calculate(column_expression, format_def)
        elif format_def.type == OutputFormatType.COMBINE:
            return self._apply_postgres_combine(column_expression, format_def)
        else:
            return column_expression
    
    def _apply_postgres_string_format(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply PostgreSQL string formatting using TO_CHAR"""
        if not format_def.format_string:
            return column_expression
        
        format_type = format_def.format_type or FormatType.DATETIME
        
        if format_type == FormatType.DATETIME:
            # Handle date/time formatting using TO_CHAR
            # Cast to TIMESTAMP to ensure proper type handling, but use user's format string
            return f"TO_CHAR({column_expression}::TIMESTAMP, '{format_def.format_string}')"
                
        elif format_type == FormatType.NUMBER:
            # Handle number formatting - cast to NUMERIC for proper handling
            return f"TO_CHAR({column_expression}::NUMERIC, '{format_def.format_string}')"
                
        elif format_type == FormatType.CURRENCY:
            # Handle currency formatting - cast to NUMERIC for proper handling
            return f"TO_CHAR({column_expression}::NUMERIC, '{format_def.format_string}')"
            
        elif format_type == FormatType.PERCENTAGE:
            # Handle percentage formatting - cast to NUMERIC for proper handling
            return f"TO_CHAR({column_expression}::NUMERIC, '{format_def.format_string}')"
            
        elif format_type == FormatType.CUSTOM:
            # Handle custom format strings - try to infer the type for casting
            # For custom formats, we'll try to cast to the most appropriate type
            if any(word in format_def.format_string.upper() for word in ['YYYY', 'MM', 'DD', 'HH', 'MI', 'SS']):
                # Looks like a date/time format
                return f"TO_CHAR({column_expression}::TIMESTAMP, '{format_def.format_string}')"
            elif any(word in format_def.format_string for word in ['9', '.', ',', '$', '%']):
                # Looks like a number format
                return f"TO_CHAR({column_expression}::NUMERIC, '{format_def.format_string}')"
            else:
                # Fallback to text formatting
                return f"TO_CHAR({column_expression}::TEXT, '{format_def.format_string}')"
            
        else:
            # Fallback to TO_CHAR with the format string
            # Try to infer the type for the fallback case
            if any(word in format_def.format_string.upper() for word in ['YYYY', 'MM', 'DD', 'HH', 'MI', 'SS']):
                return f"TO_CHAR({column_expression}::TIMESTAMP, '{format_def.format_string}')"
            else:
                return f"TO_CHAR({column_expression}::TEXT, '{format_def.format_string}')"
    
    def _apply_postgres_cast(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply PostgreSQL CAST formatting"""
        if not format_def.target_type:
            return column_expression
            
        # Map target types to PostgreSQL CAST types
        sql_type_mapping = {
            "string": "VARCHAR",
            "integer": "INTEGER", 
            "float": "DOUBLE PRECISION",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "timestamp": "TIMESTAMP"
        }
        
        sql_type = sql_type_mapping.get(format_def.target_type, "VARCHAR")
        return f"CAST({column_expression} AS {sql_type})"
    
    def _apply_postgres_calculate(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply PostgreSQL calculation formatting"""
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
    
    def _apply_postgres_combine(self, column_expression: str, format_def: OutputFormat) -> str:
        """Apply PostgreSQL combine formatting using CONCAT"""
        if not format_def.source_columns:
            return column_expression
            
        # Build CONCAT expression for combining columns
        delimiter = format_def.delimiter or " "
        
        # Start with the base column
        concat_parts = [column_expression]
        
        # Add other source columns
        for col in format_def.source_columns:
            concat_parts.append(f"'{delimiter}'")
            concat_parts.append(col)
            
        return f"CONCAT({', '.join(concat_parts)})"
    
    def _build_combine_expression(self, parts: List[Tuple[str, Optional[str]]]) -> str:
        """
        Build PostgreSQL CONCAT expression for combining multiple columns.
        
        Args:
            parts: List of (column_expression, delimiter_before_column) tuples
                   First tuple has None as delimiter
                   
        Returns:
            PostgreSQL CONCAT expression
            
        Example:
            parts = [("first_name", None), ("last_name", " ")]
            returns: CONCAT(first_name, ' ', last_name)
        """
        if len(parts) == 1:
            return parts[0][0]
        
        concat_parts = []
        for col, delimiter in parts:
            if delimiter is not None:
                # Add delimiter literal before the column
                concat_parts.append(f"'{delimiter}'")
            concat_parts.append(col)
        
        return f"CONCAT({', '.join(concat_parts)})"
