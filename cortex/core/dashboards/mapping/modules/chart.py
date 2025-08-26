from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError
from cortex.core.types.dashboards import AxisDataType


class ChartMapping(VisualizationMapping):
    """Mapping configuration for chart visualizations (bar, line, area, etc.)."""
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for chart visualization."""
        # Determine mapping mode upfront: categorical (category+value) or x/y
        uses_category_value = bool(self.data_mapping.category_field and self.data_mapping.value_field)
        # Validate only the fields that are present; this won't require x/y if not provided
        self.data_mapping.validate_against_result(result_columns)

        if not uses_category_value:
            # Charts require x and at least one y
            if not self.data_mapping.x_axis:
                raise MappingValidationError(
                    "x_axis", 
                    "Chart visualization requires an x_axis mapping"
                )
            if not (self.data_mapping.y_axes and len(self.data_mapping.y_axes) > 0):
                raise MappingValidationError(
                    "y_axes", 
                    "Chart visualization requires at least one y-axis mapping"
                )
        
        # Y-axis should typically be numerical unless using category/value
        if not uses_category_value:
            y_mappings = self.data_mapping.y_axes or []
            for ym in y_mappings:
                # Only validate data type if it's explicitly provided
                if ym.data_type and ym.data_type not in [AxisDataType.NUMERICAL]:
                    raise MappingValidationError(
                        "y_axes",
                        f"Y-axis field should be numerical, got {ym.data_type}"
                    )
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for chart visualization."""
        return ["x_axis", "y_axes"]
    
    def _get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration including stacking options."""
        config = {}
        if hasattr(self, 'chart_config') and self.chart_config:
            config.update(self.chart_config)
        return config
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for chart display."""
        if not metric_result:
            return {
                "series": [],
                "metadata": {
                    "x_label": self.data_mapping.x_axis.label if self.data_mapping.x_axis else "",
                    "y_label": (self.data_mapping.y_axes[0].label if (self.data_mapping.y_axes and len(self.data_mapping.y_axes) > 0 and self.data_mapping.y_axes[0].label) else "")
                }
            }
        
        # Support donut/pie mappings via category/value
        if self.data_mapping.category_field and self.data_mapping.value_field:
            category_field = self.data_mapping.category_field.field
            value_field = self.data_mapping.value_field.field
            points = []
            for row in metric_result:
                val = row.get(value_field)
                if val is None:
                    continue
                if not isinstance(val, (int, float)):
                    try:
                        val = float(val)
                    except Exception:
                        continue
                # ChartDataPoint requires { x, y }
                points.append({"x": row.get(category_field), "y": val})
            return {
                "series": [{"name": self.data_mapping.value_field.label or value_field, "data": points}],
                "metadata": {
                    "x_label": category_field,
                    "y_label": value_field,
                    "series_type": "categorical"
                }
            }

        x_field = self.data_mapping.x_axis.field
        series_field = self.data_mapping.series_field.field if self.data_mapping.series_field else None
        # Support multiple Y
        y_fields = []
        y_labels = []
        if self.data_mapping.y_axes and len(self.data_mapping.y_axes) > 0:
            for m in self.data_mapping.y_axes:
                y_fields.append(m.field)
                y_labels.append(m.label or m.field)
        
        if series_field:
            # Multi-series by series field (existing)
            return self._transform_multi_series(metric_result, x_field, y_fields[0], series_field)
        else:
            # Multiple Ys as separate series
            if len(y_fields) > 1:
                return self._transform_multi_y(metric_result, x_field, y_fields, y_labels)
            # Single series
            return self._transform_single_series(metric_result, x_field, y_fields[0])
    
    def _transform_single_series(self, data: List[Dict[str, Any]], x_field: str, y_field: str) -> Dict[str, Any]:
        """Transform data for single series chart to StandardChartData shape.
        Returns series with data points as {x, y} objects as expected by ChartSeries/ChartDataPoint.
        """
        points = []
        for row in data:
            x_val = row.get(x_field)
            y_raw = row.get(y_field)
            # Drop points with missing/invalid Y to satisfy ChartDataPoint typing
            if y_raw is None:
                continue
            # Coerce numeric-like strings to float
            if not isinstance(y_raw, (int, float)):
                try:
                    y_raw = float(y_raw)
                except Exception:
                    continue
            points.append({
                "x": x_val,
                "y": y_raw
            })

        chart_config = self._get_chart_config()
        return {
            "series": [{
                "name": (self.data_mapping.y_axes[0].label if (self.data_mapping.y_axes and len(self.data_mapping.y_axes) > 0 and self.data_mapping.y_axes[0].label) else y_field),
                "data": points
            }],
            "metadata": {
                "x_label": self.data_mapping.x_axis.label or x_field,
                "y_label": (self.data_mapping.y_axes[0].label if (self.data_mapping.y_axes and len(self.data_mapping.y_axes) > 0 and self.data_mapping.y_axes[0].label) else y_field),
                "series_type": "single",
                "chart_config": chart_config
            }
        }
    
    def _transform_multi_series(self, data: List[Dict[str, Any]], x_field: str, y_field: str, series_field: str) -> Dict[str, Any]:
        """Transform data for multi-series chart to StandardChartData shape."""
        # Group rows by series name
        grouped: Dict[Any, List[Dict[str, Any]]] = {}
        for row in data:
            key = row.get(series_field)
            grouped.setdefault(key, []).append(row)

        series_list = []
        for series_name, rows in grouped.items():
            points = []
            for row in rows:
                x_val = row.get(x_field)
                y_raw = row.get(y_field)
                if y_raw is None:
                    continue
                if not isinstance(y_raw, (int, float)):
                    try:
                        y_raw = float(y_raw)
                    except Exception:
                        continue
                points.append({
                    "x": x_val,
                    "y": y_raw
                })
            series_list.append({
                "name": str(series_name),
                "data": points
            })

        chart_config = self._get_chart_config()
        return {
            "series": series_list,
            "metadata": {
                "x_label": self.data_mapping.x_axis.label or x_field,
                "y_label": y_field,
                "series_label": self.data_mapping.series_field.label or series_field,
                "series_type": "multi",
                "chart_config": chart_config
            }
        }

    def _transform_multi_y(self, data: List[Dict[str, Any]], x_field: str, y_fields: List[str], y_labels: List[str]) -> Dict[str, Any]:
        series_list = []
        for idx, y_field in enumerate(y_fields):
            points = []
            for row in data:
                x_val = row.get(x_field)
                y_raw = row.get(y_field)
                if y_raw is None:
                    continue
                if not isinstance(y_raw, (int, float)):
                    try:
                        y_raw = float(y_raw)
                    except Exception:
                        continue
                points.append({"x": x_val, "y": y_raw})
            series_list.append({"name": y_labels[idx] if idx < len(y_labels) else y_field, "data": points})
        chart_config = self._get_chart_config()
        return {
            "series": series_list,
            "metadata": {
                "x_label": self.data_mapping.x_axis.label or x_field,
                "y_label": ", ".join(y_labels) if y_labels else ", ".join(y_fields),
                "series_type": "multi",
                "chart_config": chart_config
            }
        }
