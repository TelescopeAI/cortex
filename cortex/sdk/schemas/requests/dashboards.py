from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import field_validator, model_validator

from cortex.core.types.telescope import TSModel
from cortex.core.types.dashboards import (
    DashboardType,
    VisualizationType,
    ColorScheme,
    NumberFormat,
    ValueSelectionMode,
    ValueSelectionConfig,
)

from cortex.api.schemas.requests.metrics import MetricCreateRequest


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
    # Only multi-Y support; optional to allow incomplete drafts
    y_axes: Optional[List[FieldMappingRequest]] = None
    value_field: Optional[FieldMappingRequest] = None
    category_field: Optional[FieldMappingRequest] = None
    series_field: Optional[FieldMappingRequest] = None
    columns: Optional[List[ColumnMappingRequest]] = None


class SingleValueConfigRequest(TSModel):
    """Request model for single value configuration."""
    number_format: Optional[NumberFormat] = NumberFormat.DECIMAL  # Default to decimal format
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    show_comparison: bool = True
    show_trend: bool = True
    trend_period: Optional[str] = "previous_period"
    show_sparkline: bool = False
    show_title: bool = True
    show_description: bool = False
    compact_mode: bool = False
    # Value selection - default to FIRST row when multiple rows exist
    selection_mode: Optional[ValueSelectionMode] = ValueSelectionMode.FIRST
    selection_config: Optional[ValueSelectionConfig] = None


class ChartConfigRequest(TSModel):
    """Request model for chart configuration."""
    show_points: Optional[bool] = True
    line_width: Optional[int] = 2
    bar_width: Optional[float] = None
    stack_bars: bool = False
    smooth_lines: bool = False
    area_stacking_type: Optional[str] = None


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
    # Value selection - default to FIRST row when multiple rows exist
    selection_mode: Optional[ValueSelectionMode] = ValueSelectionMode.FIRST
    selection_config: Optional[ValueSelectionConfig] = None


class VisualizationConfigRequest(TSModel):
    """Request model for visualization configuration."""
    type: VisualizationType
    data_mapping: DataMappingRequest
    chart_config: Optional["ChartConfigRequest"] = None
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
    """Request model for dashboard widget creation/update.
    
    Metric can be specified either by metric_id (reference to stored metric) or
    by providing a metric object directly (inline metric definition via MetricCreateRequest).
    """
    alias: str
    section_alias: str
    metric_id: Optional[UUID] = None  # Reference to stored metric (mutually exclusive with metric)
    metric: Optional[MetricCreateRequest] = None  # Inline metric definition (mutually exclusive with metric_id)
    position: int
    grid_config: WidgetGridConfigRequest
    title: str  # Required widget title
    description: Optional[str] = None
    visualization: VisualizationConfigRequest
    metric_overrides: Optional[MetricExecutionOverridesRequest] = None
    
    @model_validator(mode='after')
    def validate_metric_specification(self):
        """Ensure exactly one of metric_id or metric is provided."""
        if self.metric_id is not None and self.metric is not None:
            raise ValueError("Cannot provide both metric_id and metric; provide exactly one")
        if self.metric_id is None and self.metric is None:
            raise ValueError("Must provide either metric_id or metric")
        return self


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
    
    @model_validator(mode='after')
    def ensure_default_section(self):
        """Ensure view has at least one section, create a default if none provided."""
        if self.sections is None or len(self.sections) == 0:
            self.sections = [
                DashboardSectionRequest(
                    alias='default',
                    title='Default',
                    description=None,
                    position=0,
                    widgets=[]
                )
            ]
        return self


class DashboardCreateRequest(TSModel):
    """Request model for dashboard creation."""
    environment_id: UUID
    alias: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: DashboardType
    views: Optional[List[DashboardViewRequest]] = None
    default_view_index: int = 0  # Index in views list to set as default
    tags: Optional[List[str]] = None
    
    @model_validator(mode='after')
    def ensure_default_view(self):
        """Ensure dashboard has at least one view, create a default if none provided."""
        if self.views is None or len(self.views) == 0:
            self.views = [
                DashboardViewRequest(
                    alias='default',
                    title='Default',
                    description=None,
                    sections=None,  # Will be populated by DashboardViewRequest validator
                    context_id=None,
                    layout=None
                )
            ]
        return self


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


DashboardWidgetRequest.model_rebuild()