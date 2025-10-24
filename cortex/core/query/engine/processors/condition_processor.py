from typing import Optional, Dict, Any, List, Union
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.conditions import Condition, WhenClause, ComparisonOperator
from cortex.core.types.semantics.column_field import ColumnField
from cortex.core.query.engine.processors.transform_processor import TransformProcessor


class ConditionProcessor(TSModel):
    """
    Converts Condition objects to SQL CASE statements.
    Handles nested transforms and database-specific syntax.
    """
    
    @staticmethod
    def process_condition(
        condition: Condition,
        table_alias_map: Optional[Dict[str, str]] = None,
        dialect: str = "postgres"
    ) -> str:
        """Convert Condition to CASE WHEN SQL"""
        parts = ["CASE"]
        
        for when_clause in condition.when_clauses:
            # Process the field with its transforms
            field_sql = ConditionProcessor._process_field(
                when_clause.field, table_alias_map, dialect
            )
            
            # Build comparison
            comparison = ConditionProcessor._build_comparison(
                field_sql, 
                when_clause.operator, 
                when_clause.compare_values,
                table_alias_map,
                dialect
            )
            
            # Process then_return value
            then_value = ConditionProcessor._process_return_value(
                when_clause.then_return, table_alias_map, dialect
            )
            
            parts.append(f"WHEN {comparison} THEN {then_value}")
        
        # Process else value
        else_value = ConditionProcessor._process_return_value(
            condition.else_return, table_alias_map, dialect
        )
        parts.append(f"ELSE {else_value}")
        parts.append("END")
        
        return " ".join(parts)
    
    @staticmethod
    def _process_field(
        field: ColumnField,
        table_alias_map: Optional[Dict[str, str]],
        dialect: str
    ) -> str:
        """Process a ColumnField through its transform pipeline"""
        # Start with column reference
        table = table_alias_map.get(field.table) if table_alias_map and field.table else field.table
        sql = f"{table}.{field.column}" if table else field.column
        
        # Apply transforms in order (pipeline!)
        if field.transforms:
            for transform in field.transforms:
                sql = TransformProcessor.process_transform(transform, sql, dialect)
        
        return sql
    
    @staticmethod
    def _build_comparison(
        field_sql: str,
        operator: ComparisonOperator,
        compare_values: Optional[Union[Any, List[Any], ColumnField]],
        table_alias_map: Optional[Dict[str, str]],
        dialect: str
    ) -> str:
        """Build comparison expression"""
        op = operator.value
        
        if operator in [ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL]:
            return f"{field_sql} {op}"
        
        # Handle ColumnField comparison
        if isinstance(compare_values, ColumnField):
            right_sql = ConditionProcessor._process_field(compare_values, table_alias_map, dialect)
            return f"{field_sql} {op} {right_sql}"
        
        # Handle IN / NOT IN with list
        if operator in [ComparisonOperator.IN, ComparisonOperator.NOT_IN]:
            if isinstance(compare_values, list):
                values_sql = ", ".join([TransformProcessor._format_value(v) for v in compare_values])
                return f"{field_sql} {op} ({values_sql})"
        
        # Handle BETWEEN
        if operator == ComparisonOperator.BETWEEN:
            if isinstance(compare_values, list) and len(compare_values) == 2:
                val1 = TransformProcessor._format_value(compare_values[0])
                val2 = TransformProcessor._format_value(compare_values[1])
                return f"{field_sql} BETWEEN {val1} AND {val2}"
        
        # Handle simple comparison
        value_sql = TransformProcessor._format_value(compare_values)
        return f"{field_sql} {op} {value_sql}"
    
    @staticmethod
    def _process_return_value(
        return_value: Union[Any, ColumnField],
        table_alias_map: Optional[Dict[str, str]],
        dialect: str
    ) -> str:
        """Process a return value (primitive or ColumnField)"""
        if isinstance(return_value, ColumnField):
            return ConditionProcessor._process_field(return_value, table_alias_map, dialect)
        return TransformProcessor._format_value(return_value)
