from typing import Optional

from core.types.semantics.measure import SemanticMeasureType, SemanticMeasureOutputFormat
from core.types.telescope import TSModel


class SemanticMeasure(TSModel):
    """
    Represents a quantitative measurement used in semantic metrics for analytics.
    
    A semantic measure defines what data should be quantified and how it should be
    calculated and formatted. It serves as a building block for semantic metrics
    and is used in generating analytical queries.
    
    Attributes:
        name: The unique identifier name for this measure
        description: A human-readable explanation of what this measure represents
        type: The calculation type (e.g., count, sum, average) to be applied
        format: Optional formatting instructions for the measure's output values
        alias: Optional alternative name to use in queries and results
        query: Optional custom query expression that defines this measure
        table: The source table or view where this measure's data resides
        primary_key: Optional identifier for the primary key column of the table
    """
    name: str
    description: Optional[str]
    type: SemanticMeasureType
    format: Optional[SemanticMeasureOutputFormat] = None
    alias: Optional[str] = None
    query: Optional[str] = None
    table: Optional[str] = None
    primary_key: Optional[str] = None
