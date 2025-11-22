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
    Service for validating metric semantic definitions and configurations.
    Performs comprehensive validation including syntax, semantics, and dependencies.
    """
    
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
        metric_errors, metric_warnings = ValidationService._check_metric(metric)
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
    
    @staticmethod
    def _check_metric(metric: SemanticMetric) -> Tuple[List[str], List[str]]:
        """Check a single metric definition."""
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
            param_errors = ValidationService._check_parameters(metric.parameters)
            errors.extend(param_errors)
        
        # Joins validation
        if metric.joins:
            join_errors = ValidationService._check_joins(metric.joins)
            errors.extend(join_errors)
        
        return errors, warnings
    
    @staticmethod
    def _check_parameters(parameters: Dict[str, Any]) -> List[str]:
        """Check metric parameters."""
        errors = []
        
        for param_name, param_def in parameters.items():
            if not param_name:
                errors.append("Parameter name cannot be empty")
            
            # Additional parameter validation can be added here
            
        return errors
    
    @staticmethod
    def _check_joins(joins: List[Any]) -> List[str]:
        """Check metric joins."""
        errors = []
        
        for i, join in enumerate(joins):
            if not hasattr(join, 'left_table') or not hasattr(join, 'right_table'):
                errors.append(f"Join {i}: missing left_table or right_table")
            
            if not hasattr(join, 'conditions') or not join.conditions:
                errors.append(f"Join {i}: missing join conditions")
        
        return errors
