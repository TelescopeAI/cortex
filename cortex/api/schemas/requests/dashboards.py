from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.types.dashboards import DashboardType, VisualizationType, ColorScheme, NumberFormat


class DashboardLayoutRequest(TSModel):
    """Request model for dashboard layout configuration."""
    layout_type: Optional[str] = None
    frontend_config: Optional[Dict[str, Any]] = None


class WidgetGridConfigRequest(TSModel):
    """Request model for widget grid configuration."""
    columns: int = 1
    rows: int = 1
    min_columns: Optional[int] = None
    min_rows: Optional[int] = None


class FieldMappingRequest(TSModel):
    """Request model for field mapping configuration."""
    field: str
    # Make optional to allow creating widgets with minimal mapping; defaults are applied server-side
    data_type: Optional[str] = None  # AxisDataType enum value
    label: Optional[str] = None
    required: Optional[bool] = False


class ColumnMappingRequest(TSModel):
    """Request model for table column mapping."""
    field: str
    label: str
    width: Optional[int] = None
    sortable: bool = True
    filterable: bool = True
    alignment: Optional[str] = None


class DataMappingRequest(TSModel):
    """Request model for data mapping configuration."""
    x_axis: Optional[FieldMappingRequest] = None
    y_axis: Optional[FieldMappingRequest] = None
    value_field: Optional[FieldMappingRequest] = None
    category_field: Optional[FieldMappingRequest] = None
    series_field: Optional[FieldMappingRequest] = None
    columns: Optional[List[ColumnMappingRequest]] = None


class SingleValueConfigRequest(TSModel):
    """Request model for single value configuration."""
    number_format: NumberFormat
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    show_comparison: bool = True
    show_trend: bool = True
    trend_period: Optional[str] = "previous_period"
    show_sparkline: bool = False
    show_title: bool = True
    show_description: bool = False
    compact_mode: bool = False


class GaugeConfigRequest(TSModel):
    """Request model for gauge configuration."""
    min_value: float = 0
    max_value: float = 100
    target_value: Optional[float] = None
    color_ranges: Optional[List[Dict[str, Any]]] = None
    show_value: bool = True
    show_target: bool = True
    gauge_type: str = "arc"
    thickness: int = 10


class VisualizationConfigRequest(TSModel):
    """Request model for visualization configuration."""
    type: VisualizationType
    data_mapping: DataMappingRequest
    single_value_config: Optional[SingleValueConfigRequest] = None
    gauge_config: Optional[GaugeConfigRequest] = None
    show_legend: bool = True
    show_grid: bool = True
    show_axes_labels: bool = True
    color_scheme: Optional[ColorScheme] = None
    custom_colors: Optional[List[str]] = None


class MetricExecutionOverridesRequest(TSModel):
    """Request model for metric execution overrides."""
    context_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None


class DashboardWidgetRequest(TSModel):
    """Request model for dashboard widget creation/update."""
    alias: str
    section_alias: str
    metric_id: UUID
    position: int
    grid_config: WidgetGridConfigRequest
    title: str  # Required widget title
    description: Optional[str] = None
    visualization: VisualizationConfigRequest
    metric_overrides: Optional[MetricExecutionOverridesRequest] = None


class DashboardSectionRequest(TSModel):
    """Request model for dashboard section creation/update."""
    alias: str
    title: Optional[str] = None
    description: Optional[str] = None
    position: int
    widgets: List[DashboardWidgetRequest]


class DashboardViewRequest(TSModel):
    """Request model for dashboard view creation/update."""
    alias: str
    title: str
    description: Optional[str] = None
    sections: Optional[List[DashboardSectionRequest]] = None
    context_id: Optional[str] = None
    layout: Optional[DashboardLayoutRequest] = None


class DashboardCreateRequest(TSModel):
    """Request model for dashboard creation."""
    environment_id: UUID
    alias: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: DashboardType
    views: List[DashboardViewRequest]
    default_view_index: int = 0  # Index in views list to set as default
    tags: Optional[List[str]] = None


class DashboardUpdateRequest(TSModel):
    """Request model for dashboard update."""
    alias: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[DashboardType] = None
    tags: Optional[List[str]] = None
    # Allow updating default view and full views structure
    default_view: Optional[str] = None
    views: Optional[List[DashboardViewRequest]] = None


class DashboardViewCreateRequest(TSModel):
    """Request model for creating a new view in existing dashboard."""
    alias: str
    title: str
    description: Optional[str] = None
    sections: Optional[List[DashboardSectionRequest]] = None
    context_id: Optional[str] = None
    layout: Optional[DashboardLayoutRequest] = None


class DashboardViewUpdateRequest(TSModel):
    """Request model for updating an existing view."""
    alias: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    context_id: Optional[str] = None
    layout: Optional[DashboardLayoutRequest] = None


class SetDefaultViewRequest(TSModel):
    """Request model for setting default view."""
    # Reference view by alias string
    view_alias: str