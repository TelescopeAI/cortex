from typing import List, Dict, Any, Optional

from cortex.core.semantics.output_formats import OutputFormat, OutputFormatType, OutputFormatMode, FormattingMap
from cortex.core.types.telescope import TSModel


class OutputProcessor(TSModel):
    """
    Processes output format definitions and applies transformations to query results.
    """
    
    @staticmethod
    def process_output_formats(data: List[Dict[str, Any]], formats: List[OutputFormat]) -> List[Dict[str, Any]]:
        """
        Apply output format transformations to query results.
        
        Args:
            data: List of result dictionaries from query execution
            formats: List of OutputFormat objects to apply
            
        Returns:
            Transformed data
        """
        if not data or not formats:
            return data
            
        # Filter formats by mode - only process POST_QUERY formats here
        post_query_formats = [f for f in formats if f.mode == OutputFormatMode.POST_QUERY]
        
        if not post_query_formats:
            return data
            
        transformed_data = data
        
        for format_def in post_query_formats:
            transformed_data = OutputProcessor._apply_single_format(transformed_data, format_def)
        
        return transformed_data
    
    @staticmethod
    def _apply_single_format(data: List[Dict[str, Any]], format_def: OutputFormat) -> List[Dict[str, Any]]:
        """
        Apply a single output format transformation.
        
        Args:
            data: List of result dictionaries
            format_def: OutputFormat object to apply
            
        Returns:
            Transformed data
        """
        if format_def.type == OutputFormatType.RAW:
            return data
        
        transformed_data = []
        
        for row in data:
            new_row = row.copy()
            
            if format_def.type == OutputFormatType.COMBINE:
                new_row = OutputProcessor._apply_combine_format(new_row, format_def)
            elif format_def.type == OutputFormatType.CALCULATE:
                new_row = OutputProcessor._apply_calculate_format(new_row, format_def)
            elif format_def.type == OutputFormatType.CAST:
                new_row = OutputProcessor._apply_cast_format(new_row, format_def)
            elif format_def.type == OutputFormatType.FORMAT:
                new_row = OutputProcessor._apply_string_format(new_row, format_def)
            # Note: AGGREGATE type would typically be handled at the query level
            
            transformed_data.append(new_row)
        
        return transformed_data
    
    @staticmethod
    def _apply_combine_format(row: Dict[str, Any], format_def: OutputFormat) -> Dict[str, Any]:
        """Apply COMBINE format transformation."""
        if not format_def.source_columns:
            return row
            
        delimiter = format_def.delimiter or " "
        values = []
        
        for col in format_def.source_columns:
            if col in row:
                values.append(str(row[col]))
        
        combined_value = delimiter.join(values)
        row[format_def.name] = combined_value
        
        return row
    
    @staticmethod
    def _apply_calculate_format(row: Dict[str, Any], format_def: OutputFormat) -> Dict[str, Any]:
        """Apply CALCULATE format transformation."""
        if not format_def.operands or len(format_def.operands) < 2:
            return row
            
        try:
            operand_values = []
            for operand in format_def.operands:
                if operand in row:
                    value = row[operand]
                    # Try to convert to number
                    if isinstance(value, str):
                        try:
                            value = float(value)
                        except ValueError:
                            continue
                    operand_values.append(value)
            
            if len(operand_values) >= 2:
                result = operand_values[0]
                
                for i in range(1, len(operand_values)):
                    if format_def.operation == "add":
                        result += operand_values[i]
                    elif format_def.operation == "subtract":
                        result -= operand_values[i]
                    elif format_def.operation == "multiply":
                        result *= operand_values[i]
                    elif format_def.operation == "divide":
                        if operand_values[i] != 0:
                            result /= operand_values[i]
                        else:
                            result = None
                            break
                
                row[format_def.name] = result
        
        except (TypeError, ValueError):
            # If calculation fails, set to None
            row[format_def.name] = None
        
        return row
    
    @staticmethod
    def _apply_cast_format(row: Dict[str, Any], format_def: OutputFormat) -> Dict[str, Any]:
        """Apply CAST format transformation."""
        if not format_def.source_columns or not format_def.target_type:
            return row
            
        for col in format_def.source_columns:
            if col in row:
                try:
                    value = row[col]
                    
                    if format_def.target_type == "string":
                        row[col] = str(value)
                    elif format_def.target_type == "integer":
                        row[col] = int(float(value))  # Handle string numbers
                    elif format_def.target_type == "float":
                        row[col] = float(value)
                    elif format_def.target_type == "boolean":
                        row[col] = bool(value)
                    # Add more type conversions as needed
                        
                except (TypeError, ValueError):
                    # If casting fails, keep original value
                    pass
        
        return row
    
    @staticmethod
    def _apply_string_format(row: Dict[str, Any], format_def: OutputFormat) -> Dict[str, Any]:
        """Apply FORMAT (string formatting) transformation."""
        if not format_def.source_columns or not format_def.format_string:
            return row
            
        for col in format_def.source_columns:
            if col in row:
                try:
                    value = row[col]
                    
                    # Apply format string (basic implementation)
                    if format_def.format_string.startswith("%."):
                        # Handle percentage formats like "%.2f"
                        if isinstance(value, (int, float)):
                            formatted_value = format_def.format_string % value
                            row[col] = formatted_value
                    else:
                        # Handle other format strings
                        formatted_value = format_def.format_string.format(value)
                        row[col] = formatted_value
                        
                except (TypeError, ValueError):
                    # If formatting fails, keep original value
                    pass
        
        return row 

    @staticmethod
    def get_in_query_formats(formats: List[OutputFormat]) -> List[OutputFormat]:
        """
        Get formats that should be applied during SQL query generation.
        
        Args:
            formats: List of OutputFormat objects
            
        Returns:
            List of formats with mode IN_QUERY
        """
        return [f for f in formats if f.mode == OutputFormatMode.IN_QUERY]
    
    @staticmethod
    def generate_in_query_sql(formats: List[OutputFormat], base_column: str) -> str:
        """
        Generate SQL expressions for IN_QUERY formats.
        
        Args:
            formats: List of OutputFormat objects with mode IN_QUERY
            base_column: The base column name to apply formatting to
            
        Returns:
            SQL expression string with all IN_QUERY formats applied
        """
        if not formats:
            return base_column
            
        # Apply formats in sequence, building up the SQL expression
        current_expression = base_column
        
        for format_def in formats:
            current_expression = OutputProcessor._apply_format_to_sql(current_expression, format_def)
            
        return current_expression
    
    @staticmethod
    def _apply_format_to_sql(column_expression: str, format_def: OutputFormat) -> str:
        """
        Apply a single format to a SQL column expression.
        
        Args:
            column_expression: Current SQL column expression
            format_def: OutputFormat to apply
            
        Returns:
            Modified SQL expression
        """
        if format_def.type == OutputFormatType.RAW:
            return column_expression
        elif format_def.type == OutputFormatType.CAST:
            return OutputProcessor._apply_cast_to_sql(column_expression, format_def)
        elif format_def.type == OutputFormatType.FORMAT:
            return OutputProcessor._apply_format_string_to_sql(column_expression, format_def)
        elif format_def.type == OutputFormatType.CALCULATE:
            return OutputProcessor._apply_calculate_to_sql(column_expression, format_def)
        elif format_def.type == OutputFormatType.COMBINE:
            return OutputProcessor._apply_combine_to_sql(column_expression, format_def)
        else:
            # Unsupported format type for IN_QUERY, return as-is
            return column_expression
    
    @staticmethod
    def _apply_cast_to_sql(column_expression: str, format_def: OutputFormat) -> str:
        """Apply CAST format to SQL expression."""
        if not format_def.target_type:
            return column_expression
            
        # Map target types to SQL CAST functions
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
    
    @staticmethod
    def _apply_format_string_to_sql(column_expression: str, format_def: OutputFormat) -> str:
        """Apply FORMAT (string formatting) to SQL expression."""
        if not format_def.format_string:
            return column_expression
            
        # Handle different format string types
        if format_def.format_string.startswith("%."):
            # Handle percentage formats like "%.2f"
            return f"TO_CHAR({column_expression}, '{format_def.format_string}')"
        elif format_def.format_string.startswith("YYYY"):
            # Handle date formats
            return f"TO_CHAR({column_expression}, '{format_def.format_string}')"
        else:
            # Handle other format strings - use CONCAT for basic string operations
            return f"CONCAT('{format_def.format_string}', {column_expression})"
    
    @staticmethod
    def _apply_calculate_to_sql(column_expression: str, format_def: OutputFormat) -> str:
        """Apply CALCULATE format to SQL expression."""
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
    
    @staticmethod
    def _apply_combine_to_sql(column_expression: str, format_def: OutputFormat) -> str:
        """Apply COMBINE format to SQL expression."""
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
    
    @staticmethod
    def collect_semantic_formatting(measures: Optional[List] = None, 
                                   dimensions: Optional[List] = None, 
                                   filters: Optional[List] = None) -> FormattingMap:
        """
        Collect all formatting definitions from semantic objects.
        
        Args:
            measures: List of SemanticMeasure objects
            dimensions: List of SemanticDimension objects  
            filters: List of SemanticFilter objects
            
        Returns:
            Dictionary mapping object names to their formatting lists
        """
        formatting_map: FormattingMap = {}
        
        # Collect from measures
        if measures:
            for measure in measures:
                if measure.formatting:
                    formatting_map[measure.name] = measure.formatting
        
        # Collect from dimensions
        if dimensions:
            for dimension in dimensions:
                if dimension.formatting:
                    formatting_map[dimension.name] = dimension.formatting
        
        # Collect from filters
        if filters:
            for filter_obj in filters:
                if filter_obj.formatting:
                    formatting_map[filter_obj.name] = filter_obj.formatting
        
        return formatting_map
    
    @staticmethod
    def apply_semantic_formatting_to_column(column_name: str, 
                                          object_name: str, 
                                          formatting_map: FormattingMap) -> str:
        """
        Apply formatting to a specific column based on semantic object formatting.
        
        Args:
            column_name: The base column name
            object_name: The name of the semantic object (measure/dimension/filter)
            formatting_map: Mapping of object names to formatting lists
            
        Returns:
            Formatted column expression
        """
        if object_name not in formatting_map:
            return column_name
            
        formats = formatting_map.get(object_name)
        return OutputProcessor.generate_in_query_sql(formats, column_name) 