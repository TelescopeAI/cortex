from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError
from cortex.core.types.dashboards import AxisDataType
from cortex.core.types.dashboards import ValueSelectionMode


class GaugeMapping(VisualizationMapping):
    """Mapping configuration for gauge visualizations."""
    
    def __init__(self, data_mapping: DataMapping, min_value: float = 0, max_value: float = 100, target_value: Optional[float] = None):
        super().__init__(data_mapping)
        self.min_value = min_value
        self.max_value = max_value
        self.target_value = target_value
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for gauge visualization."""
        # Gauge uses x_axis as the value field
        if not self.data_mapping.x_axis:
            raise MappingValidationError("x_axis", "Gauge visualization requires an x_axis mapping")
        self.data_mapping.x_axis.validate_against_result(result_columns)
        
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
        return ["x_axis"]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for gauge display."""
        if not metric_result:
            return {
                "value": None,
                "percentage": 0,
                "formatted_value": "No data",
                "gauge_config": self._get_gauge_config()
            }
        
        value_field = self.data_mapping.x_axis.field
        
        # Select value based on selection strategy
        value = self._select_value(metric_result, value_field)
        sel_mode = getattr(self, 'selection_mode', ValueSelectionMode.FIRST)
        try:
            if isinstance(value, str):
                if sel_mode == ValueSelectionMode.CONCAT:
                    # Gauge cannot render non-numeric; use None to surface gracefully
                    value = None
                else:
                    value = float(value)
        except Exception:
            if sel_mode == ValueSelectionMode.CONCAT:
                value = None
            else:
                raise MappingValidationError("x_axis", f"Gauge requires numeric data. Column '{value_field}' contains non-numeric value: {value}")
        
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
            "field_label": (self.data_mapping.x_axis.label or value_field)
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
            return (self.data_mapping.x_axis.format.show_null_as if self.data_mapping.x_axis and self.data_mapping.x_axis.format else "N/A")
        
        if not (self.data_mapping.x_axis and self.data_mapping.x_axis.format):
            return str(value)
        
        format_config = self.data_mapping.x_axis.format
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

    def _select_value(self, rows: List[Dict[str, Any]], field: str) -> Any:
        if not rows:
            return None
        mode = getattr(self, 'selection_mode', ValueSelectionMode.FIRST)
        cfg = getattr(self, 'selection_config', {}) or {}
        if mode == ValueSelectionMode.FIRST:
            return rows[0].get(field)
        if mode == ValueSelectionMode.LAST:
            return rows[-1].get(field)
        if mode == ValueSelectionMode.NTH:
            n = int(cfg.get('n', 1))
            idx = max(0, min(len(rows)-1, n-1))
            return rows[idx].get(field)
        if mode == ValueSelectionMode.CONCAT:
            delim = cfg.get('delimiter', ',')
            return delim.join([str(r.get(field)) for r in rows if r.get(field) is not None])
        if mode == ValueSelectionMode.MIN:
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            return min(values) if values else None
        if mode == ValueSelectionMode.MAX:
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            return max(values) if values else None
        if mode in (ValueSelectionMode.MEAN, ValueSelectionMode.MEDIAN, ValueSelectionMode.MODE):
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            if not values:
                return None
            if mode == ValueSelectionMode.MEAN:
                return sum(values)/len(values)
            if mode == ValueSelectionMode.MEDIAN:
                s = sorted(values)
                m = len(s)//2
                return (s[m] if len(s)%2==1 else (s[m-1]+s[m])/2)
            if mode == ValueSelectionMode.MODE:
                try:
                    from statistics import mode as stats_mode
                    return stats_mode(values)
                except Exception:
                    return sum(values)/len(values)
        if mode == ValueSelectionMode.AGGREGATE:
            how = (cfg.get('aggregate_by') or 'sum').lower()
            values = [r.get(field) for r in rows if isinstance(r.get(field), (int, float))]
            if not values:
                return None
            if how == 'sum':
                return sum(values)
            if how in ('avg', 'mean'):
                return sum(values)/len(values)
            if how == 'median':
                s = sorted(values)
                m = len(s)//2
                return (s[m] if len(s)%2==1 else (s[m-1]+s[m])/2)
            if how == 'min':
                return min(values)
            if how == 'max':
                return max(values)
            return sum(values)
        return rows[0].get(field)
