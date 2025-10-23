from typing import List, Optional, Dict, Any
from pydantic import ConfigDict

from cortex.core.types.telescope import TSModel
from cortex.core.semantics.order_sequences import SemanticOrderSequence, SemanticOrderReferenceType
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.registry import SemanticRegistry
from cortex.core.types.semantics.order import SemanticOrderType, SemanticNullsPosition
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.types.semantics.column_source import is_temporal_type, is_numeric_type
from cortex.core.query.engine.processors.output_processor import OutputProcessor


class OrderProcessor(TSModel):
    """
    Processes semantic order sequences and converts them to SQL ORDER BY clauses.
    Also handles default ordering when no explicit order is specified.
    """
    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def process_order_sequences(
        order_sequences: Optional[List[SemanticOrderSequence]] = None,
        measures: Optional[List[SemanticMeasure]] = None,
        dimensions: Optional[List[SemanticDimension]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        table_prefix: Optional[str] = None,
        formatting_map: Optional[Dict[str, List]] = None,
        apply_default_ordering: bool = True,
        is_grouped_query: bool = False,
        select_expressions: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Process a list of semantic order sequences and return an ORDER BY clause.
        If no explicit order sequences are provided and apply_default_ordering is True,
        generates default ordering based on available measures and dimensions.
        
        Supports multiple ordering paradigms:
        1. Semantic ordering by measure/dimension names (context-aware)
        2. Position-based ordering by SELECT clause position  
        3. Direct column ordering (legacy compatibility)
        
        Args:
            order_sequences: List of SemanticOrderSequence objects
            measures: List of available measures for semantic resolution and default ordering
            dimensions: List of available dimensions for semantic resolution and default ordering
            parameters: Optional runtime parameters for parameterized orders
            table_prefix: Optional table prefix for column qualification
            formatting_map: Optional formatting map for column transformations
            apply_default_ordering: Whether to apply default ordering when no explicit order is specified
            is_grouped_query: Whether the query contains GROUP BY (affects measure resolution)
            select_expressions: Dict mapping column aliases to their SELECT expressions for position/semantic resolution
            
        Returns:
            SQL ORDER BY clause string or None
        """
        if not order_sequences and not apply_default_ordering:
            return None
            
        order_clauses = []
        
        # Build semantic registry for context-aware resolution
        semantic_registry = SemanticRegistry.build_registry(
            measures, dimensions, is_grouped_query, select_expressions, formatting_map
        )
        
        # Process explicit order sequences
        if order_sequences:
            for order_seq in order_sequences:
                clause = OrderProcessor._build_order_clause(
                    order_seq, parameters, table_prefix, formatting_map, semantic_registry
                )
                if clause:
                    order_clauses.append(clause)
        
        # Apply default ordering if no explicit orders and default ordering is enabled
        elif apply_default_ordering:
            default_clause = OrderProcessor._build_default_order_clause(
                measures, dimensions, table_prefix, formatting_map, semantic_registry
            )
            if default_clause:
                order_clauses.append(default_clause)
        
        return f"ORDER BY {', '.join(order_clauses)}" if order_clauses else None

    @staticmethod
    def _build_order_clause(
        order_seq: SemanticOrderSequence,
        parameters: Optional[Dict[str, Any]] = None,
        table_prefix: Optional[str] = None,
        formatting_map: Optional[Dict[str, List]] = None,
        semantic_registry: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Optional[str]:
        """
        Build a single order clause as SQL string.
        Supports multiple ordering paradigms:
        1. Semantic ordering by measure/dimension names (context-aware)
        2. Position-based ordering by SELECT clause position
        3. Direct column ordering (legacy compatibility)
        
        Args:
            order_seq: SemanticOrderSequence object
            parameters: Optional runtime parameters
            table_prefix: Optional table prefix for column qualification
            formatting_map: Optional formatting map for column transformations
            semantic_registry: Registry mapping semantic names to SQL expressions
            
        Returns:
            SQL order clause string or None
        """
        column = None
        
        # Determine the column expression based on ordering type
        if order_seq.semantic_type == SemanticOrderReferenceType.POSITION and order_seq.position:
            # Position-based ordering (1-indexed)
            column = str(order_seq.position)
            
        elif order_seq.semantic_type in [SemanticOrderReferenceType.MEASURE, SemanticOrderReferenceType.DIMENSION]:
            # Semantic ordering by measure/dimension name
            if semantic_registry and order_seq.semantic_name:
                registry_key = f"{order_seq.semantic_type.value}s"  # "measures" or "dimensions"
                if registry_key in semantic_registry and order_seq.semantic_name in semantic_registry[registry_key]:
                    column = semantic_registry[registry_key][order_seq.semantic_name]
                    
        elif order_seq.query:
            # Legacy direct column ordering (backward compatibility)
            column = OrderProcessor._get_qualified_column_name(
                order_seq.query, order_seq.table, table_prefix
            )
            
            # Apply any formatting to the column
            if formatting_map and order_seq.name in formatting_map:
                column = OutputProcessor.apply_semantic_formatting_to_column(
                    column, order_seq.name, formatting_map
                )
        
        # Fallback: try to resolve from semantic name if no other approach worked
        if not column and order_seq.semantic_name and semantic_registry:
            # Try both measures and dimensions
            for registry_key in ["measures", "dimensions"]:
                if registry_key in semantic_registry and order_seq.semantic_name in semantic_registry[registry_key]:
                    column = semantic_registry[registry_key][order_seq.semantic_name]
                    break
        
        if not column:
            # No valid column found
            return None
        
        # Build the order clause
        clause_parts = [column]
        
        # Add order direction
        if order_seq.order_type == SemanticOrderType.DESC:
            clause_parts.append("DESC")
        else:
            clause_parts.append("ASC")
        
        # Add nulls positioning if specified
        if order_seq.nulls:
            if order_seq.nulls == SemanticNullsPosition.FIRST:
                clause_parts.append("NULLS FIRST")
            else:  # SemanticNullsPosition.LAST
                clause_parts.append("NULLS LAST")
        
        return " ".join(clause_parts)

    @staticmethod
    def _build_default_order_clause(
        measures: Optional[List[SemanticMeasure]] = None,
        dimensions: Optional[List[SemanticDimension]] = None,
        table_prefix: Optional[str] = None,
        formatting_map: Optional[Dict[str, List]] = None,
        semantic_registry: Optional[Dict[str, Dict[str, str]]] = None
    ) -> Optional[str]:
        """
        Build intelligent default order clause based on the following rules:
        1. First temporal dimension (using source_type), ascending
        2. If no temporal dimension, first temporal measure, descending  
        3. If no temporal measure, first non-temporal measure, descending
        4. If no measures, first non-temporal dimension, ascending
        
        Args:
            measures: List of available measures
            dimensions: List of available dimensions  
            table_prefix: Optional table prefix for column qualification
            formatting_map: Optional formatting map for column transformations
            
        Returns:
            Default SQL order clause string or None
        """
        # Rule 1: First temporal dimension (smart type-based detection), ascending
        if dimensions:
            # First try to find a temporal dimension using source_type
            for dim in dimensions:
                if dim.source_type and is_temporal_type(dim.source_type):
                    # For ORDER BY, use the clean alias name, not the formatted expression
                    if semantic_registry and "dimensions" in semantic_registry and dim.name in semantic_registry["dimensions"]:
                        column = semantic_registry["dimensions"][dim.name]
                    else:
                        column = OrderProcessor._get_qualified_column_name(
                            dim.query, dim.table, table_prefix
                        )
                    return f"{column} ASC"
            
            # Fallback to name-based detection for backward compatibility
            for dim in dimensions:
                if OrderProcessor._is_time_dimension_with_granularity(dim):
                    # For ORDER BY, use the clean alias name, not the formatted expression
                    if semantic_registry and "dimensions" in semantic_registry and dim.name in semantic_registry["dimensions"]:
                        column = semantic_registry["dimensions"][dim.name]
                    else:
                        column = OrderProcessor._get_qualified_column_name(
                            dim.query, dim.table, table_prefix
                        )
                    return f"{column} ASC"
        
        # Rule 2: First temporal measure, descending
        if measures:
            # First try to find a temporal measure using source_type
            for measure in measures:
                if measure.source_type and is_temporal_type(measure.source_type):
                    # For ORDER BY, use the clean alias name, not the formatted expression
                    if semantic_registry and "measures" in semantic_registry and measure.name in semantic_registry["measures"]:
                        column = semantic_registry["measures"][measure.name]
                    else:
                        column = OrderProcessor._get_qualified_column_name(
                            measure.query or measure.name, measure.table, table_prefix
                        )
                    return f"{column} DESC"
        
        # Rule 3: First non-temporal measure, descending
        if measures:
            measure = measures[0]
            # For ORDER BY, use the clean alias name, not the formatted expression
            if semantic_registry and "measures" in semantic_registry and measure.name in semantic_registry["measures"]:
                column = semantic_registry["measures"][measure.name]
            else:
                column = OrderProcessor._get_qualified_column_name(
                    measure.query or measure.name, measure.table, table_prefix
                )
            return f"{column} DESC"
        
        # Rule 4: First dimension, ascending
        if dimensions:
            dim = dimensions[0]
            # For ORDER BY, use the clean alias name, not the formatted expression
            if semantic_registry and "dimensions" in semantic_registry and dim.name in semantic_registry["dimensions"]:
                column = semantic_registry["dimensions"][dim.name]
            else:
                column = OrderProcessor._get_qualified_column_name(
                    dim.query, dim.table, table_prefix
                )
            return f"{column} ASC"
        
        return None

    @staticmethod
    def _is_time_dimension_with_granularity(dimension: SemanticDimension) -> bool:
        """
        Check if a dimension is a time dimension with granularity.
        This is a placeholder implementation - you may need to enhance this
        based on your dimension metadata or naming conventions.
        
        Args:
            dimension: SemanticDimension to check
            
        Returns:
            True if the dimension appears to be a time dimension with granularity
        """
        # Check for common time dimension indicators
        time_keywords = ['date', 'time', 'timestamp', 'created', 'updated', 'year', 'month', 'day', 'week']
        granularity_keywords = ['granularity', 'grain', 'period', 'interval']
        
        name_lower = dimension.name.lower()
        query_lower = dimension.query.lower()
        desc_lower = (dimension.description or '').lower()
        
        # Check if name, query, or description contains time-related keywords
        has_time_indicator = any(keyword in name_lower or keyword in query_lower or keyword in desc_lower 
                               for keyword in time_keywords)
        
        # For now, we'll assume any time-related dimension potentially has granularity
        # You might want to enhance this with more sophisticated logic or metadata
        return has_time_indicator


    @staticmethod
    def _get_qualified_column_name(
        column_query: str,
        table_name: Optional[str] = None,
        table_prefix: Optional[str] = None
    ) -> str:
        """Get a fully qualified column name with table prefix"""
        # Determine the prefix to use
        prefix = table_prefix or table_name
        
        if '.' in column_query:
            # Column already has a table prefix
            if prefix:
                # Replace the existing table prefix with the new one
                column_part = column_query.split('.', 1)[1]  # Get everything after the first dot
                return f"{prefix}.{column_part}"
            else:
                # No new prefix provided, return as-is
                return column_query
        else:
            # Column doesn't have a table prefix
            if prefix:
                return f'"{prefix}".{column_query}'
            return column_query
