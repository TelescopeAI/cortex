from typing import Optional, Dict, Any, List
from enum import Enum

from cortex.core.types.telescope import TSModel


class ExtensionOperation(str, Enum):
    ADD = "add"           # Add new components
    OVERRIDE = "override" # Override existing components
    FILTER = "filter"     # Add additional filters
    JOIN = "join"         # Add additional joins
    AGGREGATE = "aggregate" # Add additional aggregations


class MetricAdditions(TSModel):
    """
    Defines what to add to the base metric.
    """
    measures: Optional[List[Dict[str, Any]]] = None  # List of SemanticMeasure dicts
    dimensions: Optional[List[Dict[str, Any]]] = None  # List of SemanticDimension dicts
    joins: Optional[List[Dict[str, Any]]] = None  # List of SemanticJoin dicts
    aggregations: Optional[List[Dict[str, Any]]] = None  # List of SemanticAggregation dicts
    output_formats: Optional[List[Dict[str, Any]]] = None  # List of OutputFormat dicts
    filters: Optional[List[Dict[str, Any]]] = None  # List of SemanticFilter dicts
    limit: Optional[int] = None  # Override default limit


class MetricOverrides(TSModel):
    """
    Defines what to override in the base metric.
    """
    measures: Optional[Dict[str, Dict[str, Any]]] = None  # measure_name -> SemanticMeasure dict
    dimensions: Optional[Dict[str, Dict[str, Any]]] = None  # dimension_name -> SemanticDimension dict
    joins: Optional[Dict[str, Dict[str, Any]]] = None  # join_name -> SemanticJoin dict
    aggregations: Optional[Dict[str, Dict[str, Any]]] = None  # aggregation_name -> SemanticAggregation dict
    filters: Optional[Dict[str, Dict[str, Any]]] = None  # filter_name -> SemanticFilter dict
    output_formats: Optional[Dict[str, Dict[str, Any]]] = None  # format_name -> OutputFormat dict
    limit: Optional[int] = None  # Override default limit


class MetricExtension(TSModel):
    """
    Defines how a metric extends another metric.
    Note: This will be integrated into SemanticMetric rather than used separately.
    """
    base_metric: str  # Alias of the metric being extended
    
    # Extension operations
    add: Optional[MetricAdditions] = None
    override: Optional[MetricOverrides] = None
    
    # Extension metadata
    extension_reason: Optional[str] = None 