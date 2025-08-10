from typing import List, Dict, Any, Optional
from cortex.core.dashboards.mapping.base import VisualizationMapping, DataMapping, MappingValidationError


class TableMapping(VisualizationMapping):
    """Mapping configuration for table visualizations."""
    
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for table visualization."""
        # Validate base data mapping
        self.data_mapping.validate_against_result(result_columns)
        
        # Tables require column mappings
        if not self.data_mapping.columns or len(self.data_mapping.columns) == 0:
            raise MappingValidationError(
                "columns", 
                "Table visualization requires at least one column mapping"
            )
    
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for table visualization."""
        return ["columns"]
    
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data for table display in StandardChartData shape."""
        table_payload = {
            "columns": self._get_column_definitions(),
            "rows": [],
            "total_rows": 0,
        }
        if metric_result:
            table_payload["rows"] = self._transform_rows(metric_result)
            table_payload["total_rows"] = len(metric_result)
        # Wrap under 'table' key to match ProcessedChartData
        return {"table": table_payload}
    
    def _get_column_definitions(self) -> List[Dict[str, Any]]:
        """Get column definitions for table headers (name/type)."""
        columns: List[Dict[str, Any]] = []
        for col_mapping in self.data_mapping.columns:
            columns.append({
                "name": col_mapping.field,
                "type": "string"  # default; could be enhanced via data types
            })
        return columns
    
    def _transform_rows(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform data rows into { data: { column: value } } objects."""
        transformed_rows: List[Dict[str, Any]] = []
        column_fields = [c.field for c in self.data_mapping.columns]
        for row in data:
            row_data: Dict[str, Any] = {}
            for field in column_fields:
                row_data[field] = row.get(field)
            transformed_rows.append(row_data)
        return transformed_rows
    
    def _format_cell_value(self, value: Any, format_config: Optional[Any]) -> str:
        """Format a cell value according to formatting configuration."""
        if value is None:
            return format_config.show_null_as if format_config and format_config.show_null_as else ""
        
        if not format_config:
            return str(value)
        
        formatted = str(value)
        
        # Apply number formatting if it's a number
        if isinstance(value, (int, float)) and format_config.decimal_places is not None:
            formatted = f"{value:.{format_config.decimal_places}f}"
        
        # Apply prefix and suffix
        if format_config.prefix:
            formatted = f"{format_config.prefix}{formatted}"
        if format_config.suffix:
            formatted = f"{formatted}{format_config.suffix}"
        
        return formatted
