from typing import Optional, Dict, Any
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.transforms import Transform, TransformFunction


class TransformProcessor(TSModel):
    """
    Converts Transform objects to SQL strings.
    Handles database-specific syntax.
    """
    
    @staticmethod
    def process_transform(
        transform: Transform,
        input_sql: str,
        dialect: str = "postgres"
    ) -> str:
        """Apply a transform to input SQL expression"""
        func = transform.function.value
        params = transform.params or {}
        
        if func == "COALESCE":
            fallback = params.get("fallback", "NULL")
            fallback_sql = TransformProcessor._format_value(fallback)
            return f"COALESCE({input_sql}, {fallback_sql})"
        
        elif func == "LOWER":
            return f"LOWER({input_sql})"
        
        elif func == "UPPER":
            return f"UPPER({input_sql})"
        
        elif func == "ROUND":
            decimals = params.get("decimals", 0)
            return f"ROUND({input_sql}, {decimals})"
        
        elif func == "EXTRACT":
            part = params.get("part", "YEAR")
            if dialect in ["postgres", "bigquery"]:
                return f"EXTRACT({part} FROM {input_sql})"
            elif dialect == "mysql":
                return f"EXTRACT({part} FROM {input_sql})"
        
        elif func == "CAST":
            target_type = params.get("type", "TEXT")
            return f"CAST({input_sql} AS {target_type})"
        
        elif func == "TRIM":
            return f"TRIM({input_sql})"
        
        elif func == "ABS":
            return f"ABS({input_sql})"
        
        elif func == "CEIL":
            return f"CEIL({input_sql})"
        
        elif func == "FLOOR":
            return f"FLOOR({input_sql})"
        
        elif func == "CONCAT":
            separator = params.get("separator", "")
            if params.get("columns"):
                columns_sql = f"'{separator}'".join([f"'{col}'" for col in params["columns"]])
                return f"CONCAT({input_sql}, {columns_sql})"
            return f"CONCAT({input_sql})"
        
        elif func == "SUBSTRING":
            start = params.get("start", 1)
            length = params.get("length")
            if length:
                return f"SUBSTRING({input_sql}, {start}, {length})"
            return f"SUBSTRING({input_sql}, {start})"
        
        # Add more functions as needed
        return input_sql
    
    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for SQL"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        else:
            return str(value)
