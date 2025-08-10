from enum import Enum
from typing import Optional
from cortex.core.types.telescope import TSModel


class DashboardType(str, Enum):
    """Dashboard types for different use cases and audiences."""
    EXECUTIVE = "executive"      # High-level KPIs, minimal interaction
    OPERATIONAL = "operational"  # Real-time monitoring, alerts
    ANALYTICAL = "analytical"    # Deep dive, filtering, drill-downs
    TACTICAL = "tactical"        # Project/campaign specific


class VisualizationType(str, Enum):
    """Supported visualization types for dashboard widgets."""
    SINGLE_VALUE = "single_value"
    GAUGE = "gauge"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    AREA_CHART = "area_chart"
    PIE_CHART = "pie_chart"
    DONUT_CHART = "donut_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    TABLE = "table"


class ColorScheme(str, Enum):
    """Predefined color schemes for visualizations."""
    DEFAULT = "default"
    BLUE = "blue"
    GREEN = "green"
    RED = "red"
    PURPLE = "purple"
    ORANGE = "orange"
    CATEGORICAL = "categorical"
    SEQUENTIAL = "sequential"
    DIVERGING = "diverging"


class NumberFormat(str, Enum):
    """Number formatting options for single value displays."""
    INTEGER = "integer"
    DECIMAL = "decimal"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    ABBREVIATED = "abbreviated"  # K, M, B notation
    SCIENTIFIC = "scientific"


class ComparisonType(str, Enum):
    """Types of comparison for single value widgets."""
    PREVIOUS_PERIOD = "previous_period"
    SAME_PERIOD_LAST_YEAR = "same_period_last_year"
    TARGET = "target"
    BASELINE = "baseline"


class AxisDataType(str, Enum):
    """Data types for chart axes."""
    NUMERICAL = "numerical"
    TEMPORAL = "temporal"
    CATEGORICAL = "categorical"


class AxisMapping(TSModel):
    field: str
    type: str  # one of AxisDataType


class SeriesMapping(TSModel):
    field: Optional[str] = None
    type: Optional[str] = None


class DataMapping(TSModel):
    x_axis: AxisMapping
    y_axis: AxisMapping
    series: Optional[SeriesMapping] = None
    category: Optional[str] = None
    value_field: Optional[str] = None