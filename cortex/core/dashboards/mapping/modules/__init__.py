# Visualization-specific mapping modules
from cortex.core.dashboards.mapping.modules.single_value import SingleValueMapping
from cortex.core.dashboards.mapping.modules.chart import ChartMapping
from cortex.core.dashboards.mapping.modules.table import TableMapping
from cortex.core.dashboards.mapping.modules.gauge import GaugeMapping
from cortex.core.dashboards.mapping.modules.box_plot import BoxPlotMapping

__all__ = [
    'SingleValueMapping',
    'ChartMapping', 
    'TableMapping',
    'GaugeMapping',
    'BoxPlotMapping'
]
