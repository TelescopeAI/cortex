from typing import Dict, Any, List, Optional, Union
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.types.dashboards import VisualizationType, AxisDataType
from cortex.core.dashboards.dashboard import VisualizationConfig
from cortex.core.dashboards.mapping.factory import MappingFactory
from cortex.core.dashboards.mapping.modules.box_plot import BoxPlotMapping


class ChartDataPoint(TSModel):
    """Individual data point in a chart series."""
    x: Union[str, int, float]  # X-axis value
    y: Union[int, float]       # Y-axis value
    label: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BoxPlotDataPoint(TSModel):
    """Individual data point for box plot visualizations."""
    x: str                     # Category name
    min: float                 # Minimum value
    q1: float                  # First quartile
    median: float              # Median
    q3: float                  # Third quartile
    max: float                 # Maximum value
    outliers: Optional[List[float]] = None  # Outlier values
    label: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChartSeries(TSModel):
    """Data series for charts."""
    name: str
    data: Union[List[ChartDataPoint], List[BoxPlotDataPoint]]
    type: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CategoryData(TSModel):
    """Data for categorical visualizations (pie, donut)."""
    name: str
    value: Union[int, float]
    percentage: Optional[float] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TableColumn(TSModel):
    """Table column definition."""
    name: str
    type: str
    format: Optional[str] = None


class TableRow(TSModel):
    """Deprecated: retained for backward-compat only."""
    data: Dict[str, Any]


class TableData(TSModel):
    """Complete table data structure."""
    columns: List[TableColumn]
    rows: List[Dict[str, Any]]
    total_rows: Optional[int] = None


class TrendData(TSModel):
    """Trend information for time series data."""
    direction: str  # up, down, flat
    percentage_change: Optional[float] = None
    absolute_change: Optional[float] = None
    period: Optional[str] = None


class ChartMetadata(TSModel):
    """Metadata about chart data and formatting."""
    title: Optional[str] = None
    description: Optional[str] = None
    x_axis_title: Optional[str] = None
    y_axes_title: Optional[str] = None
    data_types: Dict[str, AxisDataType]
    formatting: Dict[str, str] = {}
    ranges: Optional[Dict[str, List[float]]] = None


class ProcessedChartData(TSModel):
    """Processed data ready for visualization."""
    # For most chart types
    series: Optional[List[ChartSeries]] = None
    
    # For categorical data (pie, donut)
    categories: Optional[List[CategoryData]] = None
    
    # For tabular data
    table: Optional[TableData] = None
    
    # For single value displays
    value: Optional[Union[int, float, str]] = None
    
    # Additional computed values
    totals: Optional[Dict[str, float]] = None
    averages: Optional[Dict[str, float]] = None
    trends: Optional[List[TrendData]] = None


class StandardChartData(TSModel):
    """
    Standardized chart data format that can be transformed for any charting library.
    Backend generates this format, frontend handles library-specific transformations.
    """
    # Raw data from metric execution
    raw: Dict[str, Any]
    
    # Processed data ready for visualization
    processed: ProcessedChartData
    
    # Metadata about the data
    metadata: ChartMetadata


class MetricExecutionResult(TSModel):
    """Result from executing a semantic metric."""
    columns: List[str]
    data: List[List[Any]]
    total_rows: Optional[int] = None
    execution_time_ms: Optional[float] = None


class DataTransformationService(TSModel):
    """
    Service for transforming metric execution results into standard chart data format.
    This service generates library-agnostic data that frontend can use with any charting library.
    """
    
    @staticmethod
    def transform_to_standard_format(
        metric_result: MetricExecutionResult,
        visualization_config: VisualizationConfig
    ) -> StandardChartData:
        """
        Transform metric execution result to standard chart data format.
        
        Args:
            metric_result: Raw result from metric execution
            visualization_config: Widget visualization configuration
            
        Returns:
            StandardChartData: Standardized format for frontend consumption
        """
        try:
            data_mapping = visualization_config.data_mapping
            viz_type = visualization_config.type
            
            # Create metadata
            metadata = ChartMetadata(
                title=f"Chart Data",  # Can be overridden by widget title
                x_axis_title=data_mapping.x_axis.get("field", "X Axis"),
                y_axes_title=(data_mapping.y_axes[0].get("field") if getattr(data_mapping, 'y_axes', None) and data_mapping.y_axes else "Y Axis"),
                data_types={
                    "x": AxisDataType(data_mapping.x_axis.get("type", "categorical")),
                    "y": AxisDataType((data_mapping.y_axes[0].get("type") if getattr(data_mapping, 'y_axes', None) and data_mapping.y_axes else "numerical"))
                }
            )
            
            # Transform based on visualization type
            if viz_type == VisualizationType.SINGLE_VALUE:
                processed = DataTransformationService._transform_single_value(
                    metric_result, data_mapping
                )
            elif viz_type in [VisualizationType.PIE_CHART, VisualizationType.DONUT_CHART]:
                processed = DataTransformationService._transform_categorical(
                    metric_result, data_mapping
                )
            elif viz_type == VisualizationType.TABLE:
                processed = DataTransformationService._transform_table(
                    metric_result, data_mapping
                )
            elif viz_type == VisualizationType.BOX_PLOT:
                # Create box plot mapping and transform data
                box_plot_mapping = BoxPlotMapping(data_mapping)
                box_plot_mapping.validate(metric_result.columns)
                processed = box_plot_mapping.transform_data(metric_result.data)
            else:
                # Default to series-based charts (line, bar, area, etc.)
                processed = DataTransformationService._transform_series(
                    metric_result, data_mapping
                )
            
            return StandardChartData(
                raw={"columns": metric_result.columns, "data": metric_result.data},
                processed=processed,
                metadata=metadata
            )
            
        except Exception as e:
            raise Exception(f"Failed to transform data: {str(e)}")
    
    @staticmethod
    def _transform_single_value(
        metric_result: MetricExecutionResult,
        data_mapping: Any
    ) -> ProcessedChartData:
        """Transform data for single value display."""
        if not metric_result.data:
            return ProcessedChartData(value=0)
        
        # Get the value field from mapping or use first numeric column
        value_field = data_mapping.value_field or (data_mapping.y_axes[0].get("field") if getattr(data_mapping, 'y_axes', None) and data_mapping.y_axes else None)
        
        if value_field:
            # Find column index
            try:
                col_index = metric_result.columns.index(value_field)
                value = metric_result.data[0][col_index] if metric_result.data else 0
            except (ValueError, IndexError):
                value = metric_result.data[0][0] if metric_result.data else 0
        else:
            # Use first row, last column (typically the measure)
            value = metric_result.data[0][-1] if metric_result.data else 0
        
        return ProcessedChartData(value=value)
    
    @staticmethod
    def _transform_categorical(
        metric_result: MetricExecutionResult,
        data_mapping: Any
    ) -> ProcessedChartData:
        """Transform data for pie/donut charts."""
        if not metric_result.data:
            return ProcessedChartData(categories=[])
        
        category_field = data_mapping.category or data_mapping.x_axis.get("field")
        value_field = data_mapping.value_field or (data_mapping.y_axes[0].get("field") if getattr(data_mapping, 'y_axes', None) and data_mapping.y_axes else None)
        
        try:
            category_index = metric_result.columns.index(category_field)
            value_index = metric_result.columns.index(value_field)
        except ValueError:
            # Fallback to first two columns
            category_index = 0
            value_index = 1 if len(metric_result.columns) > 1 else 0
        
        categories = []
        total_value = sum(row[value_index] for row in metric_result.data)
        
        for row in metric_result.data:
            value = row[value_index]
            percentage = (value / total_value * 100) if total_value > 0 else 0
            
            categories.append(CategoryData(
                name=str(row[category_index]),
                value=value,
                percentage=round(percentage, 2)
            ))
        
        return ProcessedChartData(categories=categories)
    
    @staticmethod
    def _transform_table(
        metric_result: MetricExecutionResult,
        data_mapping: Any
    ) -> ProcessedChartData:
        """Transform data for table display."""
        columns = [
            TableColumn(name=col, type="string")
            for col in metric_result.columns
        ]
        
        rows = [
            TableRow(data=dict(zip(metric_result.columns, row)))
            for row in metric_result.data
        ]
        
        table_data = TableData(
            columns=columns,
            rows=rows,
            total_rows=metric_result.total_rows or len(rows)
        )
        
        return ProcessedChartData(table=table_data)
    
    @staticmethod
    def _transform_series(
        metric_result: MetricExecutionResult,
        data_mapping: Any
    ) -> ProcessedChartData:
        """Transform data for series-based charts (line, bar, area, etc.)."""
        if not metric_result.data:
            return ProcessedChartData(series=[])
        
        x_field = data_mapping.x_axis.get("field")
        y_field = (data_mapping.y_axes[0].get("field") if getattr(data_mapping, 'y_axes', None) and data_mapping.y_axes else None)
        series_config = data_mapping.series
        
        try:
            x_index = metric_result.columns.index(x_field)
            y_index = metric_result.columns.index(y_field)
        except ValueError:
            # Fallback to first two columns
            x_index = 0
            y_index = 1 if len(metric_result.columns) > 1 else 0
        
        if series_config and series_config.get("split_by"):
            # Multi-series chart
            series = DataTransformationService._create_multi_series(
                metric_result, x_index, y_index, series_config
            )
        else:
            # Single series chart - filter out rows with None x or y values
            data_points = [
                ChartDataPoint(x=row[x_index], y=row[y_index])
                for row in metric_result.data
                if row[x_index] is not None and row[y_index] is not None
            ]
            
            series = [ChartSeries(
                name=y_field or "Value",
                data=data_points
            )]
        
        return ProcessedChartData(series=series)
    
    @staticmethod
    def _create_multi_series(
        metric_result: MetricExecutionResult,
        x_index: int,
        y_index: int,
        series_config: Dict[str, Any]
    ) -> List[ChartSeries]:
        """Create multiple series for grouped data."""
        split_by_field = series_config.get("split_by")
        
        try:
            split_index = metric_result.columns.index(split_by_field)
        except ValueError:
            # Fallback to single series - filter out rows with None x or y values
            return [ChartSeries(
                name="Value",
                data=[
                    ChartDataPoint(x=row[x_index], y=row[y_index]) 
                    for row in metric_result.data
                    if row[x_index] is not None and row[y_index] is not None
                ]
            )]
        
        # Group data by series
        series_data: Dict[str, List[ChartDataPoint]] = {}
        
        for row in metric_result.data:
            # Skip rows with None x or y values
            if row[x_index] is None or row[y_index] is None:
                continue
                
            series_name = str(row[split_index])
            if series_name not in series_data:
                series_data[series_name] = []
            
            series_data[series_name].append(ChartDataPoint(
                x=row[x_index],
                y=row[y_index]
            ))
        
        # Create series objects
        series = []
        for series_name, data_points in series_data.items():
            series.append(ChartSeries(
                name=series_name,
                data=data_points
            ))
        
        return series