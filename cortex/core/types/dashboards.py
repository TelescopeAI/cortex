from enum import Enum
from typing import Optional, List
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
    BOX_PLOT = "box_plot"
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


class ValueSelectionMode(str, Enum):
    """How to select a single value from multiple rows."""
    FIRST = "first"
    LAST = "last"
    NTH = "nth"
    AGGREGATE = "aggregate"
    CONCAT = "concat"
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"


"""
Note: AxisMapping and the duplicate DataMapping used to live here. We now use
the canonical FieldMapping and DataMapping from cortex.core.dashboards.mapping.base.
Leftover imports that referenced these should be updated.
"""


class ValueSelectionConfig(TSModel):
    """Typed configuration for selecting a value from multiple rows."""
    n: Optional[int] = None              # For NTH
    aggregate_by: Optional[str] = None   # 'sum'|'mean'|'median'|'min'|'max'
    delimiter: Optional[str] = None      # For CONCAT