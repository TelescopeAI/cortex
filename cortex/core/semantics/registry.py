from typing import Optional, List, Dict

from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.semantics.measure import SemanticMeasureType
from cortex.core.types.telescope import TSModel


class SemanticRegistry(TSModel):
    """
    Registry for mapping semantic measure/dimension names to their SQL expressions.
    This enables context-aware resolution of semantic references across different query components.
    
    The registry maintains two mappings:
    - measures: Maps measure names to their SQL expressions (aggregations, calculations, etc.)
    - dimensions: Maps dimension names to their SQL expressions (column references, transformations, etc.)
    """
    
    @staticmethod
    def build_registry(
        measures: Optional[List[SemanticMeasure]] = None,
        dimensions: Optional[List[SemanticDimension]] = None,
        is_grouped_query: bool = False,
        select_expressions: Optional[Dict[str, str]] = None,
        formatting_map: Optional[Dict[str, List]] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Build a semantic registry mapping measure/dimension names to their SQL expressions.
        This enables context-aware resolution of semantic references.
        
        Args:
            measures: List of available measures
            dimensions: List of available dimensions
            is_grouped_query: Whether the query contains GROUP BY (affects measure resolution)
            select_expressions: Dict mapping column aliases to their SELECT expressions
            formatting_map: Optional formatting map for column transformations
            
        Returns:
            Dict with 'measures' and 'dimensions' keys, each containing name->expression mappings
        """
        registry = {"measures": {}, "dimensions": {}}
        
        # Build measures registry
        if measures:
            for i, measure in enumerate(measures, 1):
                # PRIORITY: Use quoted alias name if available (for SELECT ... AS "Alias Name")
                if measure.name:
                    # Use the quoted alias name for ORDER BY (this is what we want!)
                    expression = f'"{measure.name}"'
                elif select_expressions and measure.name in select_expressions:
                    # Fallback: Use the actual SELECT expression
                    expression = select_expressions[measure.name]
                elif is_grouped_query and measure.type:
                    # Fallback: In grouped queries, use the aggregated form
                    column = measure.query or measure.name
                    if measure.type == SemanticMeasureType.COUNT:
                        expression = f'COUNT({column})'
                    elif measure.type == SemanticMeasureType.SUM:
                        expression = f'SUM({column})'
                    elif measure.type == SemanticMeasureType.AVG:
                        expression = f'AVG({column})'
                    elif measure.type == SemanticMeasureType.MIN:
                        expression = f'MIN({column})'
                    elif measure.type == SemanticMeasureType.MAX:
                        expression = f'MAX({column})'
                    else:
                        expression = column
                else:
                    # Final fallback: Raw column reference
                    expression = measure.query or measure.name
                
                # Store both by name and by position
                registry["measures"][measure.name] = expression
                registry["measures"][str(i)] = expression
        
        # Build dimensions registry  
        if dimensions:
            for i, dimension in enumerate(dimensions, 1):
                # PRIORITY: Use quoted alias name if available (for SELECT ... AS "Alias Name")
                if dimension.name:
                    # Use the quoted alias name for ORDER BY (this is what we want!)
                    expression = f'"{dimension.name}"'
                elif select_expressions and dimension.name in select_expressions:
                    # Fallback: Use the actual SELECT expression
                    expression = select_expressions[dimension.name]
                else:
                    # Final fallback: Use the dimension query
                    expression = dimension.query
                
                # Note: No formatting applied when using alias names - they're already formatted in SELECT
                
                # Store both by name and by position
                registry["dimensions"][dimension.name] = expression
                registry["dimensions"][str(i)] = expression
        
        return registry
    
    @staticmethod
    def get_aliases(
        measures: Optional[List[SemanticMeasure]] = None,
        dimensions: Optional[List[SemanticDimension]] = None
    ) -> List[str]:
        """
        Get a list of all aliases (quoted names) from measures and dimensions.
        Useful for GROUP BY and ORDER BY clauses.
        
        Args:
            measures: List of semantic measures
            dimensions: List of semantic dimensions
            
        Returns:
            List of quoted alias names (e.g., ['"Revenue"', '"Date"', '"Customer Name"'])
        """
        aliases = []
        
        if measures:
            for measure in measures:
                if measure.name:
                    aliases.append(f'"{measure.name}"')
        
        if dimensions:
            for dimension in dimensions:
                if dimension.name:
                    aliases.append(f'"{dimension.name}"')
        
        return aliases
    
    @staticmethod
    def get_dimension_aliases(dimensions: Optional[List[SemanticDimension]] = None) -> List[str]:
        """
        Get a list of dimension aliases (quoted names).
        Specifically for GROUP BY clauses where only dimensions are needed.
        
        Args:
            dimensions: List of semantic dimensions
            
        Returns:
            List of quoted dimension alias names
        """
        if not dimensions:
            return []
        
        return [f'"{dim.name}"' for dim in dimensions if dim.name]

