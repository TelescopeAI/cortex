from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError
from cortex.core.types.dashboards import AxisDataType


class GaugeMapping(VisualizationMapping):
    """Mapping configuration for gauge visualizations."""
    
    def __init__(self, data_mapping: DataMapping, min_value: float = 0, max_value: float = 100, target_value: Optional[float] = None):
        super().__init__(data_mapping)
        self.min_value = min_value
        self.max_value = max_value
        self.target_value = target_value
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for gauge visualization."""
        # Validate base data mapping
        self.data_mapping.validate_against_result(result_columns)
        
        # Gauge requires exactly one value field
        if not self.data_mapping.value_field:
            raise MappingValidationError(
                "value_field", 
                "Gauge visualization requires a value_field mapping"
            )
        
        # Value field should be numerical
        if self.data_mapping.value_field.data_type not in [AxisDataType.NUMERICAL]:
            raise MappingValidationError(
                "value_field",
                f"Value field must be numerical, got {self.data_mapping.value_field.data_type}"
            )
        
        # Validate gauge configuration
        if self.min_value >= self.max_value:
            raise MappingValidationError(
                "gauge_config",
                f"Min value ({self.min_value}) must be less than max value ({self.max_value})"
            )
        
        if self.target_value is not None and (self.target_value < self.min_value or self.target_value > self.max_value):
            raise MappingValidationError(
                "gauge_config",
                f"Target value ({self.target_value}) must be between min ({self.min_value}) and max ({self.max_value})"
            )
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for gauge visualization."""
        return ["value_field"]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for gauge display."""
        if not metric_result:
            return {
                "value": None,
                "percentage": 0,
                "formatted_value": "No data",
                "gauge_config": self._get_gauge_config()
            }
        
        value_field = self.data_mapping.value_field.field
        
        # For gauge, we typically want the first row or aggregated value
        first_row = metric_result[0]
        value = first_row.get(value_field)
        
        if value is None:
            percentage = 0
            formatted_value = "N/A"
        else:
            # Calculate percentage within gauge range
            percentage = self._calculate_percentage(value)
            formatted_value = self._format_value(value)
        
        return {
            "value": value,
            "percentage": percentage,
            "formatted_value": formatted_value,
            "gauge_config": self._get_gauge_config(),
            "field_name": value_field,
            "field_label": self.data_mapping.value_field.label or value_field
        }
    
    def _calculate_percentage(self, value: float) -> float:
        """Calculate the percentage of value within the gauge range."""
        if value is None:
            return 0
        
        # Clamp value within gauge range
        clamped_value = max(self.min_value, min(self.max_value, value))
        
        # Calculate percentage
        range_size = self.max_value - self.min_value
        if range_size == 0:
            return 0
        
        percentage = ((clamped_value - self.min_value) / range_size) * 100
        return round(percentage, 2)
    
    def _get_gauge_config(self) -> Dict[str, Any]:
        """Get gauge configuration for visualization."""
        config = {
            "min_value": self.min_value,
            "max_value": self.max_value,
            "range": self.max_value - self.min_value
        }
        
        if self.target_value is not None:
            config["target_value"] = self.target_value
            config["target_percentage"] = self._calculate_percentage(self.target_value)
        
        return config
    
    def _format_value(self, value: Any) -> str:
        """Format the value according to field formatting configuration."""
        if value is None:
            return self.data_mapping.value_field.format.show_null_as if self.data_mapping.value_field.format else "N/A"
        
        if not self.data_mapping.value_field.format:
            return str(value)
        
        format_config = self.data_mapping.value_field.format
        formatted = str(value)
        
        # Apply number formatting if it's a number
        if isinstance(value, (int, float)):
            if format_config.decimal_places is not None:
                formatted = f"{value:.{format_config.decimal_places}f}"
            else:
                formatted = str(value)
        
        # Apply prefix and suffix
        if format_config.prefix:
            formatted = f"{format_config.prefix}{formatted}"
        if format_config.suffix:
            formatted = f"{formatted}{format_config.suffix}"
        
        return formatted
