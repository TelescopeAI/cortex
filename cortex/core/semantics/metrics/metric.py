from typing import Optional, List

from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.types.telescope import TSModel


class SemanticMetric(TSModel):
    """
    Represents a semantic metric that combines measures and dimensions for analytics.
    
    A semantic metric defines what data should be measured and how it can be sliced
    for analysis. It serves as the foundation for generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this metric
        description: A human-readable explanation of what this metric represents
        query: Optional custom query string that can override the auto-generated query
        table: The source table or view where this metric's data resides
        measures: List of quantitative measurements included in this metric
        dimensions: List of categorical attributes by which the measures can be grouped
    """
    name: str
    description: Optional[str]
    query: Optional[str] = None
    table: Optional[str] = None
    measures: Optional[List[SemanticMeasure]] = None
    dimensions: Optional[List[SemanticDimension]] = None


