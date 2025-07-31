from typing import Optional

from cortex.core.types.telescope import TSModel


class SemanticDimension(TSModel):
    """
    Represents a categorical or descriptive attribute used in semantic metrics for analytics.
    
    A semantic dimension defines how data should be grouped, filtered, or categorized.
    It serves as a building block for semantic metrics and is used in generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this dimension
        description: A human-readable explanation of what this dimension represents
        query: The column name or expression that defines this dimension
        table: The source table or view where this dimension's data resides
    """
    name: str
    description: Optional[str] = None
    query: str
    table: Optional[str] = None
