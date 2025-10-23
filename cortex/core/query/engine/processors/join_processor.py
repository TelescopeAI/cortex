from typing import List, Optional, Dict
from cortex.core.semantics.joins import SemanticJoin, JoinType
from cortex.core.types.telescope import TSModel


class JoinProcessor(TSModel):
    """
    Processes join definitions and generates SQL JOIN clauses.
    Automatically handles duplicate table names by generating unique aliases.
    """
    
    @staticmethod
    def process_joins(joins: List[SemanticJoin], base_table_name: Optional[str] = None) -> Optional[str]:
        """
        Process a list of joins and generate the SQL JOIN clause.
        Automatically detects and handles duplicate table names by generating unique aliases.
        
        Args:
            joins: List of SemanticJoin objects
            base_table_name: The base table name from the FROM clause (to detect collisions)
            
        Returns:
            SQL JOIN clause string or None if no joins
        """
        if not joins:
            return None
        
        # First, detect duplicate table names and assign auto-generated aliases
        joins_with_aliases = JoinProcessor._ensure_unique_table_aliases(joins, base_table_name)
        
        join_clauses = []
        
        for join in joins_with_aliases:
            join_clause = JoinProcessor._build_single_join(join)
            if join_clause:
                join_clauses.append(join_clause)
        
        # Format joins with line breaks and proper indentation
        if len(join_clauses) > 1:
            formatted_clauses = [join_clauses[0]]  # First join
            for clause in join_clauses[1:]:
                formatted_clauses.append(f"\n{clause}")
            return " ".join(formatted_clauses)
        else:
            return " ".join(join_clauses) if join_clauses else None
    
    @staticmethod
    def build_table_alias_map(joins: List[SemanticJoin], base_table_name: Optional[str] = None) -> Dict[str, str]:
        """
        Build a mapping of original table names to their aliases from the join definitions.
        This is used by the query generator to properly qualify column names in SELECT/WHERE/etc.
        
        Args:
            joins: List of SemanticJoin objects
            base_table_name: The base table name from the FROM clause (to detect collisions)
            
        Returns:
            Dictionary mapping original table names to their aliases
            Example: {"players": "player_matches", "customers": "c"}
        """
        if not joins:
            return {}
        
        # First ensure all joins have proper aliases
        joins_with_aliases = JoinProcessor._ensure_unique_table_aliases(joins, base_table_name)
        
        # Build the mapping
        alias_map = {}
        for join in joins_with_aliases:
            if join.alias:
                # Map the original table name to its alias
                alias_map[join.right_table] = join.alias
        
        return alias_map
    
    @staticmethod
    def _ensure_unique_table_aliases(joins: List[SemanticJoin], base_table_name: Optional[str] = None) -> List[SemanticJoin]:
        """
        Ensure all joined tables have unique names by auto-generating aliases for duplicates.
        Also checks against the base table from the FROM clause.
        
        Args:
            joins: List of SemanticJoin objects
            base_table_name: The base table name from the FROM clause (to detect collisions)
            
        Returns:
            List of SemanticJoin objects with unique aliases assigned where needed
        """
        if not joins:
            return joins
        
        # Track table usage: table_name -> list of indices where it's used
        table_usage: Dict[str, List[int]] = {}
        
        # If we have a base table name, mark it as "used" (index -1 represents the FROM clause)
        if base_table_name:
            table_usage[base_table_name] = [-1]
        
        # First pass: identify all table usages in joins
        for i, join in enumerate(joins):
            table_name = join.right_table
            if table_name not in table_usage:
                table_usage[table_name] = []
            table_usage[table_name].append(i)
        
        # Second pass: assign aliases to duplicate tables
        # Track used aliases to ensure uniqueness (including the base table)
        used_aliases = set()
        if base_table_name:
            used_aliases.add(base_table_name)
        
        updated_joins = []
        for i, join in enumerate(joins):
            table_name = join.right_table
            
            # Determine if this join needs an alias:
            # 1. Table appears multiple times in joins (duplicates)
            # 2. Table name matches the base table from FROM clause (collision)
            # Note: if base_table_name is in table_usage, it will have at least [-1, ...] entries
            has_duplicates = len(table_usage.get(table_name, [])) > 1
            collides_with_base = (base_table_name is not None) and (table_name == base_table_name)
            needs_alias = has_duplicates or collides_with_base
            
            if needs_alias:
                if not join.alias:
                    # Generate a unique alias based on the table name and its occurrence number
                    occurrence_index = table_usage[table_name].index(i)
                    
                    # Try to generate a meaningful alias from the join conditions
                    # For example, if joining on "player_id", use "players_player" 
                    alias_suffix = JoinProcessor._generate_alias_suffix(join, occurrence_index)
                    auto_alias = f"{table_name}_{alias_suffix}"
                    
                    # Ensure the alias is truly unique by appending a number if needed
                    base_alias = auto_alias
                    counter = 1
                    while auto_alias in used_aliases:
                        auto_alias = f"{base_alias}_{counter}"
                        counter += 1
                    
                    used_aliases.add(auto_alias)
                    
                    # Create a copy of the join with the new alias
                    join_copy = join.model_copy(deep=True)
                    join_copy.alias = auto_alias
                    
                    # Update ALL references to the table in conditions (both left and right side)
                    # This ensures the ON clause uses the correct aliased table name
                    for condition in join_copy.conditions:
                        if condition.left_table == table_name:
                            condition.left_table = auto_alias
                        if condition.right_table == table_name:
                            condition.right_table = auto_alias
                    
                    updated_joins.append(join_copy)
                else:
                    # Join already has an alias, track it and use it as is
                    used_aliases.add(join.alias)
                    updated_joins.append(join)
            else:
                # No duplicates, but still track the alias if present
                if join.alias:
                    used_aliases.add(join.alias)
                # Use the join as is
                updated_joins.append(join)
        
        return updated_joins
    
    @staticmethod
    def _generate_alias_suffix(join: SemanticJoin, occurrence_index: int) -> str:
        """
        Generate a meaningful alias suffix based on the join conditions.
        Always includes occurrence_index to ensure uniqueness.
        
        Args:
            join: SemanticJoin object
            occurrence_index: The index of this occurrence (0 for first, 1 for second, etc.)
            
        Returns:
            A meaningful alias suffix string
        """
        # Try to extract a meaningful suffix from the left table in the join condition
        if join.conditions and len(join.conditions) > 0:
            first_condition = join.conditions[0]
            left_table = first_condition.left_table
            
            # Use the left table name as part of the alias for clarity
            # e.g., "players" joined from "match_performances" becomes "players_match_performance_1"
            # e.g., "players" joined from "payments" becomes "players_payment_2"
            if left_table:
                # Singularize or abbreviate the table name for the suffix
                suffix = left_table.rstrip('s') if left_table.endswith('s') else left_table
                # Always append the occurrence index to ensure uniqueness
                return f"{suffix}_{occurrence_index + 1}"
        
        # Fallback: use numeric suffix
        return str(occurrence_index + 1)
    
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
        
        # Build the complete JOIN clause with proper indentation
        on_clause = " AND ".join(conditions)
        
        if join.alias:
            return f"{join_type_sql} {join.right_table} AS {join.alias}\n  ON {on_clause}"
        else:
            return f"{join_type_sql} {join.right_table}\n  ON {on_clause}"
    
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