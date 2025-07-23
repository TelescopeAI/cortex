from typing import List, Optional
from cortex.core.semantics.joins import SemanticJoin, JoinType
from cortex.core.types.telescope import TSModel


class JoinProcessor(TSModel):
    """
    Processes join definitions and generates SQL JOIN clauses.
    """
    
    @staticmethod
    def process_joins(joins: List[SemanticJoin]) -> Optional[str]:
        """
        Process a list of joins and generate the SQL JOIN clause.
        
        Args:
            joins: List of SemanticJoin objects
            
        Returns:
            SQL JOIN clause string or None if no joins
        """
        if not joins:
            return None
            
        join_clauses = []
        
        for join in joins:
            join_clause = JoinProcessor._build_single_join(join)
            if join_clause:
                join_clauses.append(join_clause)
        
        return " ".join(join_clauses) if join_clauses else None
    
    @staticmethod
    def _build_single_join(join: SemanticJoin) -> str:
        """
        Build a single JOIN clause from a SemanticJoin.
        
        Args:
            join: SemanticJoin object
            
        Returns:
            SQL JOIN clause string
        """
        join_type_sql = JoinProcessor._get_join_type_sql(join.join_type)
        right_table = join.alias if join.alias else join.right_table
        
        # Build conditions
        conditions = []
        for condition in join.conditions:
            condition_sql = f"{condition.left_table}.{condition.left_column} {condition.operator} {condition.right_table}.{condition.right_column}"
            conditions.append(condition_sql)
        
        # Add additional conditions if present
        if join.additional_conditions:
            for condition in join.additional_conditions:
                condition_sql = f"{condition.left_table}.{condition.left_column} {condition.operator} {condition.right_table}.{condition.right_column}"
                conditions.append(condition_sql)
        
        # Build the complete JOIN clause
        on_clause = " AND ".join(conditions)
        
        if join.alias:
            return f"{join_type_sql} {join.right_table} AS {join.alias} ON {on_clause}"
        else:
            return f"{join_type_sql} {join.right_table} ON {on_clause}"
    
    @staticmethod
    def _get_join_type_sql(join_type: JoinType) -> str:
        """
        Convert JoinType enum to SQL JOIN syntax.
        
        Args:
            join_type: JoinType enum value
            
        Returns:
            SQL JOIN type string
        """
        join_type_mapping = {
            JoinType.INNER: "INNER JOIN",
            JoinType.LEFT: "LEFT JOIN",
            JoinType.RIGHT: "RIGHT JOIN",
            JoinType.FULL: "FULL OUTER JOIN",
            JoinType.CROSS: "CROSS JOIN"
        }
        
        return join_type_mapping.get(join_type, "INNER JOIN") 