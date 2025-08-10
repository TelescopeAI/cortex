from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError
from cortex.core.types.dashboards import AxisDataType


class SingleValueMapping(VisualizationMapping):
    """Mapping configuration for single value visualizations."""
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for single value visualization."""
        # Validate base data mapping
        self.data_mapping.validate_against_result(result_columns)
        
        # Single value requires exactly one value field
        if not self.data_mapping.value_field:
            raise MappingValidationError(
                "value_field", 
                "Single value visualization requires a value_field mapping"
            )
        
        # Value field should be numerical
        if self.data_mapping.value_field.data_type not in [AxisDataType.NUMERICAL]:
            raise MappingValidationError(
                "value_field",
                f"Value field must be numerical, got {self.data_mapping.value_field.data_type}"
            )
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for single value visualization."""
        return ["value_field"]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for single value display."""
        if not metric_result:
            return {"value": None, "formatted_value": "No data"}
        
        value_field = self.data_mapping.value_field.field
        
        # For single value, we typically want the first row or aggregated value
        # This could be enhanced based on aggregation configuration
        first_row = metric_result[0]
        value = first_row.get(value_field)
        
        # Apply formatting if configured
        formatted_value = self._format_value(value)
        
        return {
            "value": value,
            "formatted_value": formatted_value,
            "field_name": value_field,
            "field_label": self.data_mapping.value_field.label or value_field
        }
    
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
