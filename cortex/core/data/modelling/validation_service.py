from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from cortex.core.data.modelling.model import DataModel
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.telescope import TSModel


class ValidationResult(TSModel):
    """
    Represents the result of a validation operation.
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_at: datetime
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ValidationService(TSModel):
    """
    Service for validating DataModel semantic definitions and configurations.
    Performs comprehensive validation including syntax, semantics, and dependencies.
    """
    
    @staticmethod
    def validate_data_model(data_model: DataModel) -> ValidationResult:
        """
        Perform comprehensive validation of a DataModel.
        
        Args:
            data_model: DataModel to validate
            
        Returns:
            ValidationResult containing validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        # Basic model validation
        basic_errors = ValidationService._validate_basic_model_structure(data_model)
        errors.extend(basic_errors)
        
        # NOTE: Semantic model validation is now handled at the metric level
        # since semantic_model field was removed from DataModel
        
        # NOTE: Metric validation is now handled separately through the metrics API
        # since metrics are no longer embedded in the data model
        
        # NOTE: Dependency validation is now handled at the metric level
        # since metrics are stored separately
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now()
        )
    
    @staticmethod
    def _validate_basic_model_structure(data_model: DataModel) -> List[str]:
        """Validate basic model structure and required fields."""
        errors = []
        
        if not data_model.name:
            errors.append("Model name is required")
        
        if data_model.version < 1:
            errors.append("Model version must be >= 1")
        
        return errors
    
    @staticmethod
    def _validate_semantic_model(data_model: DataModel) -> Tuple[List[str], List[str]]:
        """
        Validate semantic model JSON structure.
        NOTE: This method is deprecated since semantic_model field was removed from DataModel.
        Semantic validation is now handled at the metric level.
        """
        errors = []
        warnings = []
        warnings.append("Semantic model validation is now handled at the metric level")
        return errors, warnings
    
    @staticmethod
    def _validate_metrics(data_model: DataModel) -> Tuple[List[str], List[str]]:
        """
        Validate individual metrics within the semantic model.
        NOTE: This method is deprecated since metrics are no longer embedded in DataModel.
        Metric validation is now handled through the metrics API.
        """
        errors = []
        warnings = []
        warnings.append("Metric validation is now handled through the metrics API")
        return errors, warnings
    
    @staticmethod
    def _validate_single_metric(metric: SemanticMetric) -> Tuple[List[str], List[str]]:
        """Validate a single metric definition."""
        errors = []
        warnings = []
        
        # Basic required fields
        if not metric.name:
            errors.append("Name is required")
        
        # Table or query validation
        if not metric.table_name and not metric.query:
            errors.append("Either 'table_name' or 'query' must be specified")
        
        # Measures and dimensions validation
        if not metric.measures and not metric.dimensions and not metric.aggregations:
            warnings.append("No measures, dimensions, or aggregations defined - will use SELECT *")
        
        # Extension validation
        if metric.extends:
            if metric.extends == metric.alias or metric.extends == metric.name:
                errors.append("Metric cannot extend itself")
        
        # Parameters validation
        if metric.parameters:
            param_errors = ValidationService._validate_parameters(metric.parameters)
            errors.extend(param_errors)
        
        # Joins validation
        if metric.joins:
            join_errors = ValidationService._validate_joins(metric.joins)
            errors.extend(join_errors)
        
        return errors, warnings
    
    @staticmethod
    def _validate_parameters(parameters: Dict[str, Any]) -> List[str]:
        """Validate metric parameters."""
        errors = []
        
        for param_name, param_def in parameters.items():
            if not param_name:
                errors.append("Parameter name cannot be empty")
            
            # Additional parameter validation can be added here
            
        return errors
    
    @staticmethod
    def _validate_joins(joins: List[Any]) -> List[str]:
        """Validate metric joins."""
        errors = []
        
        for i, join in enumerate(joins):
            if not hasattr(join, 'left_table') or not hasattr(join, 'right_table'):
                errors.append(f"Join {i}: missing left_table or right_table")
            
            if not hasattr(join, 'conditions') or not join.conditions:
                errors.append(f"Join {i}: missing join conditions")
        
        return errors
    
    @staticmethod
    def _validate_dependencies(data_model: DataModel) -> List[str]:
        """Validate metric dependencies and extensions."""
        # Dependency validation is now handled at the metric level via the metrics API.
        # The modelling MetricService has been removed.
        return []
    
    @staticmethod
    def validate_metric_execution(metric: SemanticMetric, data_model: DataModel) -> ValidationResult:
        """
        Validate that a specific metric can be executed.
        
        Args:
            metric: SemanticMetric to validate
            data_model: DataModel containing the metric
            
        Returns:
            ValidationResult for the specific metric execution
        """
        errors = []
        warnings = []
        
        # Validate the specific metric
        metric_errors, metric_warnings = ValidationService._validate_single_metric(metric)
        errors.extend(metric_errors)
        warnings.extend(metric_warnings)
        
        # Check if metric is public
        if not metric.public:
            warnings.append(f"Metric '{metric.alias or metric.name}' is not public")
        
        # Validate that the metric belongs to the data model
        if metric.data_model_id != data_model.id:
            errors.append(f"Metric data_model_id ({metric.data_model_id}) does not match data model id ({data_model.id})")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_at=datetime.now()
        ) 