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
    def resolve_metric_extensions(data_model: DataModel, metric: SemanticMetric) -> SemanticMetric:
        """
        Resolve metric extensions by merging base metric with extension definitions.
        NOTE: Since metrics are now stored separately, this method returns the metric as-is.
        Extension resolution would require fetching the base metric from the metrics API.
        
        Args:
            data_model: DataModel containing all metrics
            metric: SemanticMetric that may extend another metric
            
        Returns:
            The metric as-is since base metrics are stored separately
        """
        if not metric.extends:
            return metric
        
        # Since metrics are now stored separately, we can't easily resolve extensions
        # without making additional API calls. For now, return the metric as-is.
        # TODO: Implement extension resolution by fetching base metrics from the API
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
    def get_metric_dependencies(data_model: DataModel, metric_alias: str) -> List[str]:
        """
        Get the list of metric aliases that the given metric depends on (through extensions).
        
        Args:
            data_model: DataModel containing all metrics
            metric_alias: Alias of the metric to analyze
            
        Returns:
            List of metric aliases that this metric depends on
        """
        dependencies = []
        visited = set()
        
        def _collect_dependencies(alias: str):
            if alias in visited:
                return  # Avoid circular dependencies
            
            visited.add(alias)
            metric = MetricService.get_metric_by_alias(data_model, alias)
            
            if metric and metric.extends:
                dependencies.append(metric.extends)
                _collect_dependencies(metric.extends)
        
        _collect_dependencies(metric_alias)
        return dependencies 