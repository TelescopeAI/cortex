from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.types.dashboards import DashboardType, VisualizationType, ColorScheme, NumberFormat, ValueSelectionMode
from cortex.api.schemas.responses.metrics import MetricResponse


class DashboardLayoutResponse(TSModel):
    """Response model for dashboard layout configuration."""
    layout_type: Optional[str]
    frontend_config: Optional[Dict[str, Any]]


class WidgetGridConfigResponse(TSModel):
    """Response model for widget grid configuration."""
    columns: int
    rows: int
    min_columns: Optional[int]
    min_rows: Optional[int]


class FieldMappingResponse(TSModel):
    """Response model for field mapping configuration."""
    field: str
    data_type: Optional[str] = None
    label: Optional[str] = None
    required: Optional[bool] = False


class ColumnMappingResponse(TSModel):
    """Response model for table column mapping."""
    field: str
    label: Optional[str] = None
    width: Optional[int] = None
    sortable: Optional[bool] = False
    filterable: Optional[bool] = False
    alignment: Optional[str] = None


class DataMappingResponse(TSModel):
    """Response model for data mapping configuration."""
    x_axis: Optional[FieldMappingResponse] = None
    y_axes: Optional[List[FieldMappingResponse]] = None
    value_field: Optional[FieldMappingResponse] = None
    category_field: Optional[FieldMappingResponse] = None
    series_field: Optional[FieldMappingResponse] = None
    columns: Optional[List[ColumnMappingResponse]] = None


class ChartConfigResponse(TSModel):
    """Response model for chart configuration."""
    show_points: bool
    line_width: int
    bar_width: Optional[float]
    stack_bars: bool
    smooth_lines: bool
    area_stacking_type: Optional[str]


class ValueSelectionConfigResponse(TSModel):
    """Response model for value selection configuration."""
    n: Optional[int] = None
    aggregate_by: Optional[str] = None
    delimiter: Optional[str] = None


class SingleValueConfigResponse(TSModel):
    """Response model for single value configuration."""
    number_format: NumberFormat
    prefix: Optional[str]
    suffix: Optional[str]
    show_comparison: bool
    show_trend: bool
    trend_period: Optional[str]
    show_sparkline: bool
    show_title: bool
    show_description: bool
    compact_mode: bool
    selection_mode: Optional[ValueSelectionMode]
    selection_config: Optional[ValueSelectionConfigResponse]


class GaugeConfigResponse(TSModel):
    """Response model for gauge configuration."""
    min_value: float
    max_value: float
    target_value: Optional[float]
    color_ranges: Optional[List[Dict[str, Any]]]
    show_value: bool
    show_target: bool
    gauge_type: str
    thickness: int
    selection_mode: Optional[ValueSelectionMode]
    selection_config: Optional[ValueSelectionConfigResponse]


class VisualizationConfigResponse(TSModel):
    """Response model for visualization configuration."""
    type: VisualizationType
    data_mapping: DataMappingResponse
    chart_config: Optional["ChartConfigResponse"]
    single_value_config: Optional[SingleValueConfigResponse]
    gauge_config: Optional[GaugeConfigResponse]
    show_legend: bool
    show_grid: bool
    show_axes_labels: bool
    color_scheme: Optional[ColorScheme]
    custom_colors: Optional[List[str]]


class MetricExecutionOverridesResponse(TSModel):
    """Response model for metric execution overrides."""
    context_id: Optional[str]
    filters: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, Any]]
    limit: Optional[int]


class DashboardWidgetResponse(TSModel):
    """Response model for dashboard widget.
    
    Supports both metric_id (reference to stored metric) and metric (embedded metric).
    Exactly one of metric_id or metric must be provided.
    """
    alias: str
    section_alias: str
    metric_id: Optional[UUID] = None  # Reference to stored metric
    metric: Optional[MetricResponse] = None  # Embedded metric definition
    position: int
    grid_config: WidgetGridConfigResponse
    title: str
    description: Optional[str]
    visualization: VisualizationConfigResponse
    metric_overrides: Optional[MetricExecutionOverridesResponse]


class DashboardSectionResponse(TSModel):
    """Response model for dashboard section."""
    alias: str
    title: Optional[str]
    description: Optional[str]
    position: int
    widgets: List[DashboardWidgetResponse]


class DashboardViewResponse(TSModel):
    """Response model for dashboard view."""
    alias: str
    title: str
    description: Optional[str]
    sections: List[DashboardSectionResponse]
    context_id: Optional[str]
    layout: Optional[DashboardLayoutResponse]
    created_at: datetime
    updated_at: datetime


class DashboardResponse(TSModel):
    """Response model for dashboard."""
    id: UUID
    alias: Optional[str]
    environment_id: UUID
    name: str
    description: Optional[str]
    type: DashboardType
    views: List[DashboardViewResponse]
    default_view: str
    tags: Optional[List[str]]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    last_viewed_at: Optional[datetime]


class DashboardListResponse(TSModel):
    """Response model for dashboard list."""
    dashboards: List[DashboardResponse]
    total: int


# Dashboard execution response models
class ChartDataPointResponse(TSModel):
    """Response model for chart data point."""
    x: Any
    y: Any
    label: Optional[str]
    category: Optional[str]
    metadata: Optional[Dict[str, Any]]


class BoxPlotDataPointResponse(TSModel):
    """Response model for box plot data point."""
    x: str
    min: float
    q1: float
    median: float
    q3: float
    max: float
    outliers: Optional[List[float]]
    label: Optional[str]
    category: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ChartSeriesResponse(TSModel):
    """Response model for chart series."""
    name: str
    data: Union[List[ChartDataPointResponse], List[BoxPlotDataPointResponse]]
    type: Optional[str]
    color: Optional[str]
    metadata: Optional[Dict[str, Any]]


class CategoryDataResponse(TSModel):
    """Response model for category data."""
    name: str
    value: Any
    percentage: Optional[float]
    color: Optional[str]
    metadata: Optional[Dict[str, Any]]


class TableColumnResponse(TSModel):
    """Response model for table column."""
    name: str
    type: str
    format: Optional[str]


class TableRowResponse(TSModel):
    """Deprecated; rows now return plain dicts. Kept for compatibility."""
    data: Dict[str, Any]


class TableDataResponse(TSModel):
    """Response model for table data."""
    columns: List[TableColumnResponse]
    rows: List[Dict[str, Any]]
    total_rows: Optional[int]


class ProcessedChartDataResponse(TSModel):
    """Response model for processed chart data."""
    series: Optional[List[ChartSeriesResponse]]
    categories: Optional[List[CategoryDataResponse]]
    table: Optional[TableDataResponse]
    value: Optional[Any]
    totals: Optional[Dict[str, float]]
    averages: Optional[Dict[str, float]]


class ChartMetadataResponse(TSModel):
    """Response model for chart metadata."""
    title: Optional[str]
    description: Optional[str]
    x_axis_title: Optional[str]
    y_axes_title: Optional[str]
    data_types: Dict[str, str]
    formatting: Dict[str, str]
    ranges: Optional[Dict[str, List[float]]]


class StandardChartDataResponse(TSModel):
    """Response model for standard chart data."""
    raw: Dict[str, Any]
    processed: ProcessedChartDataResponse
    metadata: ChartMetadataResponse


class WidgetExecutionResponse(TSModel):
    """Response model for widget execution."""
    widget_alias: str  # Use alias instead of UUID
    data: StandardChartDataResponse
    execution_time_ms: Optional[float]
    error: Optional[str]


class DashboardViewExecutionResponse(TSModel):
    """Response model for dashboard view execution."""
    view_alias: str  # Use alias instead of UUID
    widgets: List[WidgetExecutionResponse]
    total_execution_time_ms: Optional[float]
    errors: List[str]


class DashboardExecutionResponse(TSModel):
    """Response model for dashboard execution."""
    dashboard_id: UUID
    view_alias: str  # Use alias instead of UUID
    view_execution: DashboardViewExecutionResponse
    total_execution_time_ms: Optional[float]