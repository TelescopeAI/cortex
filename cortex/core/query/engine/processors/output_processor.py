from typing import List, Dict, Any, Optional
from cortex.core.semantics.output_formats import OutputFormat, OutputFormatType
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
            
        transformed_data = data
        
        for format_def in formats:
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