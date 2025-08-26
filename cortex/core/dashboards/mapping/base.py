from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.types.dashboards import AxisDataType, NumberFormat


class MappingValidationError(Exception):
    """Raised when data mapping validation fails."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Mapping validation error for field '{field}': {message}")


class FieldFormat(TSModel):
    """Configuration for field formatting and display."""
    
    number_format: Optional[NumberFormat] = None
    decimal_places: Optional[int] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    date_format: Optional[str] = None
    show_null_as: Optional[str] = None


class FieldMapping(TSModel):
    """Maps a field from metric results to visualization requirements."""
    
    field: str  # Column name from metric execution result
    data_type: Optional[AxisDataType] = None  # Expected data type, optional for backend inference
    label: Optional[str] = None  # Display name for the field
    format: Optional[FieldFormat] = None  # Formatting options
    required: bool = True  # Whether this field is required for the visualization
    
    def validate_against_result(self, result_columns: List[str]) -> None:
        """Validate that the mapped field exists in the metric result."""
        if self.field not in result_columns:
            raise MappingValidationError(
                self.field,
                f"Field '{self.field}' not found in metric result columns: {result_columns}"
            )


class ColumnMapping(TSModel):
    """Extended field mapping for table visualizations."""
    
    field: str
    label: str
    width: Optional[int] = None  # Column width in pixels
    sortable: bool = True
    filterable: bool = True
    format: Optional[FieldFormat] = None
    alignment: Optional[str] = None  # left, center, right
    
    def validate_against_result(self, result_columns: List[str]) -> None:
        """Validate that the mapped field exists in the metric result."""
        if self.field not in result_columns:
            raise MappingValidationError(
                self.field,
                f"Field '{self.field}' not found in metric result columns: {result_columns}"
            )


class DataMapping(TSModel):
    """Base class for all data mapping configurations."""
    
    # Core field mappings - optional to support different visualization types
    x_axis: Optional[FieldMapping] = None
    # Only multi-Y support
    y_axes: Optional[List[FieldMapping]] = None
    value_field: Optional[FieldMapping] = None
    category_field: Optional[FieldMapping] = None
    series_field: Optional[FieldMapping] = None
    
    # Table-specific mappings
    columns: Optional[List[ColumnMapping]] = None
    
    def get_all_fields(self) -> List[str]:
        """Get all field names referenced in this mapping."""
        fields = []
        
        if self.x_axis:
            fields.append(self.x_axis.field)
        if self.y_axes:
            fields.extend([m.field for m in self.y_axes])
        if self.value_field:
            fields.append(self.value_field.field)
        if self.category_field:
            fields.append(self.category_field.field)
        if self.series_field:
            fields.append(self.series_field.field)
        if self.columns:
            fields.extend([col.field for col in self.columns])
            
        return list(set(fields))  # Remove duplicates
    
    def validate_against_result(self, result_columns: List[str]) -> None:
        """Validate all field mappings against metric result columns."""
        if self.x_axis:
            self.x_axis.validate_against_result(result_columns)
        if self.y_axes:
            for m in self.y_axes:
                m.validate_against_result(result_columns)
        if self.value_field:
            self.value_field.validate_against_result(result_columns)
        if self.category_field:
            self.category_field.validate_against_result(result_columns)
        if self.series_field:
            self.series_field.validate_against_result(result_columns)
        if self.columns:
            for column in self.columns:
                column.validate_against_result(result_columns)


class VisualizationMapping(ABC):
    """Abstract base class for visualization-specific mapping configurations."""
    
    def __init__(self, data_mapping: DataMapping):
        self.data_mapping = data_mapping
    
    @abstractmethod
    def validate(self, result_columns: List[str]) -> None:
        """Validate that the mapping is valid for this visualization type."""
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Get the list of fields required for this visualization type."""
        pass
    
    @abstractmethod
    def transform_data(self, metric_result: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Transform metric result data according to the mapping configuration."""
        pass
