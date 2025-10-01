from typing import Optional
from enum import Enum

from cortex.core.types.telescope import TSModel
from cortex.core.types.semantics.order import SemanticOrderType, SemanticNullsPosition


class SemanticOrderReferenceType(str, Enum):
    """Types of ordering references in semantic metrics."""
    MEASURE = "measure"      # Reference to a measure by name
    DIMENSION = "dimension"  # Reference to a dimension by name  
    COLUMN = "column"        # Direct column reference (legacy)
    POSITION = "position"    # Position-based ordering (1-indexed)


class SemanticOrderSequence(TSModel):
    """
    Represents an ordering specification used in semantic metrics for sorting query results.
    
    Supports multiple ordering paradigms:
    1. Semantic ordering by measure/dimension names (recommended)
    2. Position-based ordering by SELECT clause position
    3. Direct column ordering (legacy compatibility)
    
    The processor will automatically resolve semantic references to appropriate SQL
    based on query context (grouped vs raw queries).
    
    Attributes:
        name: The unique identifier name for this order sequence
        description: A human-readable explanation of what this ordering represents
        
        # Semantic ordering (recommended approach)
        semantic_type: Type of semantic reference (measure, dimension, column, position)
        semantic_name: Name of the measure/dimension to order by
        
        # Position-based ordering
        position: 1-based position in SELECT clause for ordering
        
        # Direct column ordering (Not recommended)
        query: The column name or expression that defines the sorting criteria
        table: The source table or view where this order column resides
        
        # Common ordering properties
        order_type: The sort direction (ascending or descending)
        nulls: Optional specification of where null values should appear in the sort order
    """
    name: str
    description: Optional[str] = None
    
    # Semantic ordering approach (recommended)
    semantic_type: Optional[SemanticOrderReferenceType] = None
    semantic_name: Optional[str] = None  # Name of measure/dimension
    
    # Position-based ordering
    position: Optional[int] = None  # 1-based position in SELECT clause
    
    # Direct column approach (Not recommended)
    query: Optional[str] = None  # Column name or expression to order by
    table: Optional[str] = None
    
    # Common properties
    order_type: SemanticOrderType = SemanticOrderType.ASC
    nulls: Optional[SemanticNullsPosition] = None
    
    def get_order_reference(self) -> str:
        """
        Get the primary ordering reference based on available data.
        Priority: semantic_name > position > query
        """
        if self.semantic_name:
            return self.semantic_name
        elif self.position:
            return str(self.position)
        elif self.query:
            return self.query
        else:
            return self.name
