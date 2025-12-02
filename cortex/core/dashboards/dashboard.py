from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID, uuid4

import pytz
from pydantic import Field, model_validator

from cortex.core.dashboards.mapping.base import DataMapping as MappingDataMapping
from cortex.core.types.dashboards import (
    DashboardType, VisualizationType, ColorScheme,
    NumberFormat, ComparisonType, ValueSelectionMode, ValueSelectionConfig
)
from cortex.core.types.telescope import TSModel
from cortex.core.semantics.metrics.metric import SemanticMetric


class Dashboard(TSModel):
    """
    Core dashboard definition that combines semantic metrics into a cohesive view.
    Each dashboard is tied to a specific environment and contains multiple views.
    Frontend handles all layout, theming, and visual presentation.
    """
    id: UUID = Field(default_factory=uuid4)
    alias: Optional[str] = None  # Human-readable identifier for external references
    environment_id: UUID  # Tied to specific environment (no workspace_id needed)
    name: str
    description: Optional[str] = None
    type: DashboardType
    
    # Views management
    views: List["DashboardView"]
    # Default view referenced by alias string
    default_view: str
    
    # Metadata
    tags: Optional[List[str]] = None
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    last_viewed_at: Optional[datetime] = None


class DashboardLayout(TSModel):
    """
    Optional layout configuration hints for frontend.
    Frontend has complete control over implementation.
    """
    layout_type: Optional[str] = None
    frontend_config: Optional[Dict[str, Any]] = None


class DashboardView(TSModel):
    """
    A specific view within a dashboard. Each view can have different metrics,
    layouts, and configurations while sharing the dashboard's environment context.
    """
    alias: str  # Required alias for referencing within dashboard
    title: str  # Display name for the view
    description: Optional[str] = None
    
    # Ordered sections within this view
    sections: List["DashboardSection"]
    
    # Context awareness (like metric execution)
    context_id: Optional[str] = None  # Context for metric execution
    
    # Optional layout hints (frontend controlled)
    layout: Optional[DashboardLayout] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))


class DashboardSection(TSModel):
    """
    Logical grouping of related metrics/widgets within a dashboard view.
    Sections are ordered within a view.
    All display settings (collapsible, visibility) controlled by frontend.
    """
    alias: str  # Required alias for referencing within dashboard
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Position within the view
    position: int  # Position within the view (0-based)
    
    # Ordered widgets within this section
    widgets: List["DashboardWidget"]


class WidgetGridConfig(TSModel):
    """
    Grid configuration using relative rows and columns instead of absolute sizes.
    Frontend can translate these to any layout system.
    """
    columns: int = 1
    rows: int = 1
    min_columns: Optional[int] = None
    min_rows: Optional[int] = None


class MetricExecutionOverrides(TSModel):
    """
    Allows widgets to override view's context, filters, parameters, and limit.
    """
    context_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None


class DataMapping(MappingDataMapping):
    pass


class ChartConfig(TSModel):
    """
    Chart-specific configuration options.
    """
    show_points: bool = True
    line_width: int = 2
    bar_width: Optional[float] = None
    stack_bars: bool = False
    smooth_lines: bool = False
    area_stacking_type: Optional[Literal['normal', 'gradient']] = None


class TableConfig(TSModel):
    """
    Table-specific configuration options.
    """
    show_header: bool = True
    sortable: bool = True
    pagination: bool = True
    page_size: int = 10
    searchable: bool = False


class ComparisonConfig(TSModel):
    """
    Configuration for single value comparison display.
    """
    comparison_type: ComparisonType
    show_absolute_change: bool = True
    show_percentage_change: bool = True
    comparison_value: Optional[float] = None  # For target/baseline comparisons


class SingleValueConfig(TSModel):
    """
    Configuration for single value displays (KPI cards).
    """
    number_format: Optional[NumberFormat] = NumberFormat.DECIMAL  # Default to decimal format
    prefix: Optional[str] = None
    suffix: Optional[str] = None
    show_comparison: bool = True
    comparison_config: Optional[ComparisonConfig] = None
    show_trend: bool = True
    trend_period: Optional[str] = "previous_period"
    show_sparkline: bool = False
    show_title: bool = True
    show_description: bool = False
    compact_mode: bool = False
    # Selection strategy when multiple rows exist
    selection_mode: Optional[ValueSelectionMode] = ValueSelectionMode.FIRST
    selection_config: Optional[ValueSelectionConfig] = None


class GaugeConfig(TSModel):
    """
    Configuration for gauge visualizations.
    """
    min_value: float = 0
    max_value: float = 100
    target_value: Optional[float] = None
    color_ranges: Optional[List[Dict[str, Any]]] = None  # [{"min": 0, "max": 50, "color": "red"}]
    show_value: bool = True
    show_target: bool = True
    gauge_type: str = "arc"  # arc, linear
    thickness: int = 10
    # Optional value selection like SingleValue
    selection_mode: ValueSelectionMode = ValueSelectionMode.FIRST
    selection_config: Optional[ValueSelectionConfig] = None


class VisualizationConfig(TSModel):
    """
    Complete visualization configuration for a widget.
    """
    type: VisualizationType
    data_mapping: DataMapping
    
    # Type-specific configurations
    chart_config: Optional[ChartConfig] = None
    table_config: Optional[TableConfig] = None
    single_value_config: Optional[SingleValueConfig] = None
    gauge_config: Optional[GaugeConfig] = None
    
    # General display options
    show_legend: bool = True
    show_grid: bool = True
    show_axes_labels: bool = True
    color_scheme: Optional[ColorScheme] = None
    custom_colors: Optional[List[str]] = None


class DashboardWidget(TSModel):
    """
    Individual widget containing a semantic metric with display configuration.
    Widgets inherit the environment and context from their parent view.
    Uses relative positioning (rows/columns) instead of absolute sizing.
    
    Metric can be specified either by metric_id (reference to stored metric) or
    by providing a metric object directly (inline metric definition).
    """
    alias: str  # Required alias for referencing within dashboard
    section_alias: str  # Reference to DashboardSection by alias
    metric_id: Optional[UUID] = None  # Reference to stored SemanticMetric (mutually exclusive with metric)
    metric: Optional[SemanticMetric] = None  # Inline metric definition (mutually exclusive with metric_id)
    
    # Position within section
    position: int  # Position within the section (0-based)
    
    # Grid dimensions (relative, not absolute)
    grid_config: WidgetGridConfig
    
    # Display configuration
    title: str  # Required widget title for display
    description: Optional[str] = None
    visualization: VisualizationConfig
    
    # Metric execution overrides (can override view's context)
    metric_overrides: Optional[MetricExecutionOverrides] = None

    @model_validator(mode='after')
    def validate_metric_specification(self):
        """Ensure exactly one of metric_id or metric is provided."""
        if self.metric_id is not None and self.metric is not None:
            raise ValueError("Cannot provide both metric_id and metric; provide exactly one")
        if self.metric_id is None and self.metric is None:
            raise ValueError("Must provide either metric_id or metric")
        return self


# Forward references for Pydantic - import SemanticMetric before rebuilding
# to resolve the forward reference in DashboardWidget
DashboardWidget.model_rebuild()
DashboardSection.model_rebuild()
DashboardView.model_rebuild()
Dashboard.model_rebuild()