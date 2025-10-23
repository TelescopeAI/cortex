from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError

class BoxPlotMapping(VisualizationMapping):
    """Mapping configuration for box plot visualizations.
    
    Returns standardized box plot data format compatible with multiple charting libraries.
    Frontend components can transform this to library-specific formats (ECharts, Chart.js, etc.)
    """
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for box plot visualization."""
        self.data_mapping.validate_against_result(result_columns)
        
        # Box plots require x_axis (for category grouping) and y_axes (for data distribution)
        if not self.data_mapping.x_axis:
            raise MappingValidationError(
                "x_axis", 
                "Box plot visualization requires an x_axis for category grouping"
            )
        if not self.data_mapping.y_axes or len(self.data_mapping.y_axes) == 0:
            raise MappingValidationError(
                "y_axes",
                "Box plot visualization requires at least one y-axis for the data distribution"
            )
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for box plot visualization."""
        return ["x_axis", "y_axes"]
    
    def _calculate_quartiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate quartiles using simple, reliable statistical methods.
        
        Uses basic percentile calculation that always produces valid results.
        """
        n = len(values)
        if n == 0:
            return {}
        
        sorted_values = sorted(values)
        
        def simple_percentile(data: List[float], p: float) -> float:
            """Calculate percentile using simple linear interpolation."""
            if len(data) == 1:
                return data[0]
            
            # Simple method: p * (n - 1)
            index = p * (n - 1)
            lower = int(index)
            upper = min(lower + 1, n - 1)
            
            if lower == upper:
                return data[lower]
            
            weight = index - lower
            return data[lower] * (1 - weight) + data[upper] * weight
        
        # Calculate basic quartiles
        q1 = simple_percentile(sorted_values, 0.25)
        median = simple_percentile(sorted_values, 0.50)
        q3 = simple_percentile(sorted_values, 0.75)
        
        # For box plots, use actual min/max for whiskers
        # This ensures we never have min > max
        min_val = sorted_values[0]
        max_val = sorted_values[-1]
        
        result = {
            "min": min_val,
            "q1": q1,
            "median": median,
            "q3": q3,
            "max": max_val
        }
        
        # Ensure statistical validity - this should never be needed with proper calculation
        if result["min"] > result["max"]:
            result["min"] = result["max"]
        if result["q1"] > result["median"]:
            result["q1"] = result["median"]
        if result["median"] > result["q3"]:
            result["median"] = result["q3"]
        if result["q1"] > result["q3"]:
            result["q1"] = result["q3"]
        
        return result
    
    def _detect_outliers(self, values: List[float], q1: float, q3: float) -> List[float]:
        """Detect outliers using IQR method (1.5 * IQR beyond Q1/Q3)."""
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return [v for v in values if v < lower_bound or v > upper_bound]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data into standardized box plot format.
        
        Returns data in a library-agnostic format with explicit property names.
        Frontend components transform this to their specific charting library format.
        """
        if not metric_result:
            return {
                "series": [],
                "metadata": {
                    "x_label": "",
                    "y_label": "",
                    "series_type": "box_plot"
                }
            }
        
        x_field = self.data_mapping.x_axis.field
        y_field = self.data_mapping.y_axes[0].field  # Use first y-axis for box plot
        
        print(f"Box plot mapping - x_field: {x_field}, y_field: {y_field}")
        print(f"Sample metric_result rows: {metric_result[:3] if metric_result else 'No data'}")
        
        # Group values by category
        grouped_data: Dict[Any, List[float]] = {}
        for row in metric_result:
            category = row.get(x_field)
            value = row.get(y_field)
            
            print(f"Processing row: category={category}, value={value}")
            
            if category is None or value is None:
                print(f"Skipping row - category or value is None")
                continue
            
            # Convert value to float
            try:
                value = float(value)
            except (ValueError, TypeError):
                print(f"Skipping row - value {value} cannot be converted to float")
                continue
            
            if category not in grouped_data:
                grouped_data[category] = []
            grouped_data[category].append(value)
        
        print(f"Grouped data summary: {len(grouped_data)} categories")
        for cat, vals in list(grouped_data.items())[:5]:  # Show first 5 categories
            print(f"  {cat}: {len(vals)} values - {vals[:10]}...")
        
        # Calculate box plot statistics for each category
        box_plot_data = []
        for category in sorted(grouped_data.keys()):
            values = grouped_data[category]
            if not values:
                continue
            
            # Debug: Check the raw values before calculation
            print(f"Processing category {category} with {len(values)} values")
            print(f"Raw values: {values[:20]}...")  # Show first 20 values
            print(f"Min value: {min(values)}, Max value: {max(values)}")
            
            # Handle single-value categories by creating a simple box
            if len(values) < 2:
                print(f"Single value category {category} - creating simple box with value {values[0]}")
                # For single values, create a box with the value as center and some width
                single_value = values[0]
                # Create a small box around the single value
                box_width = max(0.1, abs(single_value) * 0.1) if single_value != 0 else 0.1
                
                data_point = {
                    "x": str(category),
                    "min": single_value - box_width,
                    "q1": single_value - box_width/2,
                    "median": single_value,
                    "q3": single_value + box_width/2,
                    "max": single_value + box_width
                }
                
                box_plot_data.append(data_point)
                continue
            
            stats = self._calculate_quartiles(values)
            if not stats:
                continue
            
            # Detect outliers
            outliers = self._detect_outliers(values, stats['q1'], stats['q3'])
            
            # Debug logging (can be removed in production)
            print(f"Box plot data for category {category}: {stats}")
            print(f"Values: {values[:10]}...")  # Show first 10 values
            print(f"Stats validation: min={stats['min']}, q1={stats['q1']}, median={stats['median']}, q3={stats['q3']}, max={stats['max']}")
            
            # Validate the result
            if stats['min'] > stats['max'] or stats['q1'] > stats['median'] or stats['median'] > stats['q3']:
                print(f"ERROR: Invalid stats detected for category {category}!")
                print(f"Original values: {values}")
                print(f"Sorted values: {sorted(values)}")
                print(f"Invalid stats: {stats}")
            
            # Create standardized box plot data point with corrected stats
            data_point = {
                "x": str(category),
                "min": stats['min'],
                "q1": stats['q1'],
                "median": stats['median'],
                "q3": stats['q3'],
                "max": stats['max']
            }
            
            # Include outliers if any exist
            if outliers:
                data_point["outliers"] = outliers
            
            box_plot_data.append(data_point)
        
        return {
            "series": [{
                "name": self.data_mapping.y_axes[0].label or y_field,
                "data": box_plot_data
            }],
            "metadata": {
                "x_label": self.data_mapping.x_axis.label or x_field,
                "y_label": self.data_mapping.y_axes[0].label or y_field,
                "series_type": "box_plot"
            }
        }
