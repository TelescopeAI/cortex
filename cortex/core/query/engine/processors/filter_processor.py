from typing import List, Optional, Dict, Any
from pydantic import ConfigDict

from cortex.core.types.telescope import TSModel
from cortex.core.semantics.filters import SemanticFilter
from cortex.core.types.semantics.filter import FilterOperator, FilterType
from cortex.core.query.engine.processors.output_processor import OutputProcessor
from cortex.core.utils.schema_inference import get_qualified_column_name


class FilterProcessor(TSModel):
    """
    Processes semantic filters and converts them to SQL WHERE and HAVING clauses.
    """
    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def process_filters(filters: Optional[List[SemanticFilter]], 
                       parameters: Optional[Dict[str, Any]] = None,
                       table_prefix: Optional[str] = None,
                       formatting_map: Optional[Dict[str, List]] = None) -> tuple[Optional[str], Optional[str]]:
        """
        Process a list of semantic filters and return WHERE and HAVING clauses.
        
        Args:
            filters: List of SemanticFilter objects
            parameters: Optional runtime parameters for parameterized filters
            table_prefix: Optional table prefix for column qualification
            
        Returns:
            Tuple of (where_clause, having_clause) - both can be None
        """
        if not filters:
            return None, None
        
        where_filters = []
        having_filters = []
        
        for filter_obj in filters:
            if not filter_obj.is_active:
                continue
                
            # Generate SQL condition for this filter
            condition = FilterProcessor._build_filter_condition(
                filter_obj, parameters, table_prefix, formatting_map
            )
            
            if condition:
                if filter_obj.filter_type == FilterType.WHERE:
                    where_filters.append(condition)
                else:  # FilterType.HAVING
                    having_filters.append(condition)
        
        # Combine conditions
        where_clause = " AND ".join(where_filters) if where_filters else None
        having_clause = " AND ".join(having_filters) if having_filters else None
        
        return where_clause, having_clause

    @staticmethod
    def _build_filter_condition(filter_obj: SemanticFilter, 
                               parameters: Optional[Dict[str, Any]] = None,
                               table_prefix: Optional[str] = None,
                               formatting_map: Optional[Dict[str, List]] = None) -> Optional[str]:
        """
        Build a single filter condition as SQL string.
        
        Args:
            filter_obj: SemanticFilter object
            parameters: Optional runtime parameters
            table_prefix: Optional table prefix for column qualification
            
        Returns:
            SQL condition string or None if filter should be skipped
        """
        # Use custom expression if provided
        if filter_obj.custom_expression:
            return FilterProcessor._substitute_parameters(
                filter_obj.custom_expression, parameters
            )
        
        # Get qualified column name
        column = get_qualified_column_name(
            column_query=filter_obj.query,
            table_name=filter_obj.table,
            table_prefix=table_prefix,
            has_joins=False  # FilterProcessor doesn't have access to joins info
        )
        
        # Apply any IN_QUERY formatting to the column
        if formatting_map and filter_obj.name in formatting_map:
            column = OutputProcessor.apply_semantic_formatting_to_column(
                column, filter_obj.name, formatting_map
            )
        
        # Get the value (could be a $CORTEX_ placeholder that was already substituted)
        value = filter_obj.value
        
        # Build condition based on operator
        if filter_obj.operator is None:
            return None  # Skip if no operator and no custom expression
        
        return FilterProcessor._build_operator_condition(
            column, filter_obj.operator, value, filter_obj
        )


    @staticmethod
    def _build_operator_condition(column: str, 
                                 operator: FilterOperator, 
                                 value: Any,
                                 filter_obj: SemanticFilter) -> str:
        """Build SQL condition based on the operator type"""
        
        if operator == FilterOperator.EQUALS:
            if value is None:
                return f"{column} IS NULL"
            return f"{column} = {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.NOT_EQUALS:
            if value is None:
                return f"{column} IS NOT NULL"
            return f"{column} != {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.GREATER_THAN:
            return f"{column} > {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.GREATER_THAN_EQUALS:
            return f"{column} >= {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.LESS_THAN:
            return f"{column} < {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.LESS_THAN_EQUALS:
            return f"{column} <= {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.IN:
            if filter_obj.values:
                values = filter_obj.values
            else:
                values = [value] if not isinstance(value, list) else value
            formatted_values = [FilterProcessor._format_value(v) for v in values]
            return f"{column} IN ({', '.join(formatted_values)})"
            
        elif operator == FilterOperator.NOT_IN:
            if filter_obj.values:
                values = filter_obj.values
            else:
                values = [value] if not isinstance(value, list) else value
            formatted_values = [FilterProcessor._format_value(v) for v in values]
            return f"{column} NOT IN ({', '.join(formatted_values)})"
            
        elif operator == FilterOperator.LIKE:
            return f"{column} LIKE {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.NOT_LIKE:
            return f"{column} NOT LIKE {FilterProcessor._format_value(value)}"
            
        elif operator == FilterOperator.IS_NULL:
            return f"{column} IS NULL"
            
        elif operator == FilterOperator.IS_NOT_NULL:
            return f"{column} IS NOT NULL"
            
        elif operator == FilterOperator.BETWEEN:
            min_val = filter_obj.min_value if filter_obj.min_value is not None else value[0] if isinstance(value, (list, tuple)) and len(value) >= 2 else None
            max_val = filter_obj.max_value if filter_obj.max_value is not None else value[1] if isinstance(value, (list, tuple)) and len(value) >= 2 else None
            
            if min_val is not None and max_val is not None:
                return f"{column} BETWEEN {FilterProcessor._format_value(min_val)} AND {FilterProcessor._format_value(max_val)}"
            return None
            
        elif operator == FilterOperator.NOT_BETWEEN:
            min_val = filter_obj.min_value if filter_obj.min_value is not None else value[0] if isinstance(value, (list, tuple)) and len(value) >= 2 else None
            max_val = filter_obj.max_value if filter_obj.max_value is not None else value[1] if isinstance(value, (list, tuple)) and len(value) >= 2 else None
            
            if min_val is not None and max_val is not None:
                return f"{column} NOT BETWEEN {FilterProcessor._format_value(min_val)} AND {FilterProcessor._format_value(max_val)}"
            return None
        
        # Default case - treat as equals
        return f"{column} = {FilterProcessor._format_value(value)}"

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for SQL inclusion"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (list, tuple)):
            formatted_values = [FilterProcessor._format_value(v) for v in value]
            return f"({', '.join(formatted_values)})"
        else:
            return f"'{str(value)}'"

    @staticmethod
    def _substitute_parameters(expression: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Substitute parameters in a custom expression - DEPRECATED: Use base_sql.py instead"""
        # This method is deprecated - parameter substitution is now handled in base_sql.py
        # to avoid double substitution and double quoting issues
        return expression 