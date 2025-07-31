from typing import List, Optional, Dict, Any
from uuid import UUID

from cortex.core.data.modelling.model import DataModel
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.telescope import TSModel


class MetricService(TSModel):
    """
    Service for extracting and managing metrics from DataModel's embedded semantic model JSON.
    Handles metric validation, resolution, and extension processing.
    """
    
    @staticmethod
    def extract_metrics_from_model(data_model: DataModel) -> List[SemanticMetric]:
        """
        Extract individual metrics from a data model's semantic model JSON.
        NOTE: This method is deprecated since semantic_model field was removed from DataModel.
        Metrics are now stored separately and accessed through the metrics API.
        
        Args:
            data_model: DataModel containing semantic model JSON
            
        Returns:
            Empty list since metrics are no longer embedded in the model
        """
        # Return empty list since metrics are now stored separately
        return []
    
    @staticmethod
    def get_metric_by_alias(data_model: DataModel, alias: str) -> Optional[SemanticMetric]:
        """
        Get a specific metric by alias from a data model.
        NOTE: This method is deprecated since metrics are no longer embedded in DataModel.
        Use the metrics API to retrieve metrics by data_model_id.
        
        Args:
            data_model: DataModel to search
            alias: Alias of the metric to find
            
        Returns:
            None since metrics are no longer embedded in the model
        """
        # Return None since metrics are now stored separately
        return None
    
    @staticmethod
    def get_metric_by_id(data_model: DataModel, metric_id: UUID) -> Optional[SemanticMetric]:
        """
        Get a specific metric by ID from a data model.
        NOTE: This method is deprecated since metrics are no longer embedded in DataModel.
        Use the metrics API to retrieve metrics by ID.
        
        Args:
            data_model: DataModel to search
            metric_id: ID of the metric to find
            
        Returns:
            None since metrics are no longer embedded in the model
        """
        # Return None since metrics are now stored separately
        return None
    
    @staticmethod
    def validate_metric_in_model(data_model: DataModel, metric_alias: str) -> bool:
        """
        Validate that a metric exists in the data model.
        NOTE: This method is deprecated since metrics are no longer embedded in DataModel.
        Use the metrics API to validate metric existence.
        
        Args:
            data_model: DataModel to validate against
            metric_alias: Alias of the metric to validate
            
        Returns:
            False since metrics are no longer embedded in the model
        """
        # Return False since metrics are now stored separately
        return False
    
    @staticmethod
    def resolve_metric_extensions(metric: SemanticMetric) -> SemanticMetric:
        """
        Resolve metric extensions by applying base metric configurations.
        
        Args:
            metric: The metric to resolve
            
        Returns:
            Resolved metric with extensions applied
        """
        # For now, metric extension has no effect - return the metric as-is
        # The extends field is a UUID pointing to a parent metric ID
        # TODO: Implement extension resolution by fetching parent metrics from the database
        return metric
    
    @staticmethod
    def _apply_additions(metric: SemanticMetric, additions: Any) -> None:
        """Apply additions from metric extension."""
        # This would implement the logic to add measures, dimensions, joins, etc.
        # For now, this is a placeholder for the addition logic
        pass
    
    @staticmethod
    def _apply_overrides(metric: SemanticMetric, overrides: Any) -> None:
        """Apply overrides from metric extension."""
        # This would implement the logic to override measures, dimensions, joins, etc.
        # For now, this is a placeholder for the override logic
        pass
    
    @staticmethod
    def get_metric_dependencies(metric: SemanticMetric) -> List[UUID]:
        """
        Get the list of metric UUIDs that the given metric depends on (through extensions).
        
        Args:
            metric: The metric to analyze
            
        Returns:
            List of metric UUIDs that this metric depends on
        """
        dependencies = []
        
        # For now, just return the direct parent if it exists
        # TODO: Implement recursive dependency resolution by fetching parent metrics from database
        if metric.extends:
            dependencies.append(metric.extends)
        
        return dependencies 