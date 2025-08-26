import time
from typing import Optional, List, Dict, Any
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.exceptions.dashboards import (
    DashboardDoesNotExistError, DashboardViewDoesNotExistError,
    DashboardWidgetDoesNotExistError, DashboardExecutionError, WidgetExecutionError
)
from cortex.core.dashboards.db.dashboard_service import DashboardCRUD
from cortex.core.dashboards.transformers import (
    DataTransformationService, StandardChartData, MetricExecutionResult
)
from cortex.core.dashboards.mapping.factory import MappingFactory
from cortex.core.dashboards.mapping.base import MappingValidationError


class WidgetExecutionResult(TSModel):
    """Result of executing a single widget."""
    widget_id: UUID
    data: StandardChartData
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


class DashboardViewExecutionResult(TSModel):
    """Result of executing a dashboard view."""
    view_id: UUID
    widgets: List[WidgetExecutionResult]
    total_execution_time_ms: Optional[float] = None
    errors: List[str] = []


class DashboardExecutionResult(TSModel):
    """Result of executing a dashboard."""
    dashboard_id: UUID
    view_id: UUID
    view_execution: DashboardViewExecutionResult
    total_execution_time_ms: Optional[float] = None


class DashboardExecutionService(TSModel):
    """
    Service for executing dashboards and widgets.
    Handles metric execution and data transformation to standard format.
    """
    
    @staticmethod
    def execute_dashboard(dashboard_id: UUID, view_alias: Optional[str] = None) -> DashboardExecutionResult:
        """
        Execute a dashboard (or specific view) and return chart data for all widgets.
        
        Args:
            dashboard_id: ID of the dashboard to execute
            view_alias: Optional specific view alias, uses default view if not provided
            
        Returns:
            DashboardExecutionResult: Execution results with widget data
        """
        start_time = time.time()
        
        try:
            # Get dashboard
            dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
            if dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)
            
            # Determine which view to execute
            target_view_alias = view_alias or dashboard.default_view
            target_view = None
            
            for view in dashboard.views:
                if view.alias == target_view_alias:
                    target_view = view
                    break
            
            if target_view is None:
                raise DashboardViewDoesNotExistError(target_view_alias)
            
            # Execute the view
            view_result = DashboardExecutionService.execute_view(dashboard_id, target_view_alias)
            
            total_time = (time.time() - start_time) * 1000
            
            return DashboardExecutionResult(
                dashboard_id=dashboard_id,
                view_id=target_view_alias,
                view_execution=view_result,
                total_execution_time_ms=total_time
            )
            
        except Exception as e:
            raise DashboardExecutionError(dashboard_id, str(e))
    
    @staticmethod
    def execute_view(dashboard_id: UUID, view_alias: str) -> DashboardViewExecutionResult:
        """
        Execute a specific dashboard view and return chart data for all widgets.
        
        Args:
            dashboard_id: ID of the dashboard
            view_alias: Alias of the view to execute
            
        Returns:
            DashboardViewExecutionResult: Execution results for the view
        """
        start_time = time.time()
        
        try:
            # Get dashboard
            dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
            if dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)
            
            # Find the view
            target_view = None
            for view in dashboard.views:
                if view.alias == view_alias:
                    target_view = view
                    break
            
            if target_view is None:
                raise DashboardViewDoesNotExistError(view_alias)
            
            # Execute all widgets in the view
            widget_results = []
            errors = []
            
            for section in target_view.sections:
                for widget in section.widgets:
                    try:
                        widget_result = DashboardExecutionService.execute_widget(
                            dashboard_id, view_alias, widget.alias
                        )
                        widget_results.append(widget_result)
                    except Exception as e:
                        error_msg = f"Widget {widget.alias} failed: {str(e)}"
                        errors.append(error_msg)
                        
                        # Add error result for widget
                        widget_results.append(WidgetExecutionResult(
                            widget_alias=widget.alias,
                            data=StandardChartData(
                                raw={},
                                processed={},
                                metadata={}
                            ),
                            error=error_msg
                        ))
            
            total_time = (time.time() - start_time) * 1000
            
            return DashboardViewExecutionResult(
                view_id=view_alias,
                widgets=widget_results,
                total_execution_time_ms=total_time,
                errors=errors
            )
            
        except Exception as e:
            raise DashboardExecutionError(dashboard_id, str(e))
    
    @staticmethod
    def execute_widget(dashboard_id: UUID, view_alias: str, widget_alias: str) -> WidgetExecutionResult:
        """
        Execute a specific widget and return its chart data.
        
        Args:
            dashboard_id: ID of the dashboard
            view_alias: Alias of the view  
            widget_alias: Alias of the widget to execute
            
        Returns:
            WidgetExecutionResult: Execution result for the widget
        """
        start_time = time.time()
        
        try:
            # Get dashboard and find widget
            dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
            if dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)
            
            # Find the view
            target_view = None
            for view in dashboard.views:
                if view.alias == view_alias:
                    target_view = view
                    break
            
            if target_view is None:
                raise DashboardViewDoesNotExistError(view_alias)
            
            # Find the widget
            target_widget = None
            for section in target_view.sections:
                for widget in section.widgets:
                    if widget.alias == widget_alias:
                        target_widget = widget
                        break
                if target_widget:
                    break
            
            if target_widget is None:
                raise DashboardWidgetDoesNotExistError(widget_alias)
            
            # Execute the metric for this widget
            metric_result = DashboardExecutionService._execute_metric(
                target_widget, target_view
            )
            
            # Transform using field mapping
            chart_data = DashboardExecutionService._transform_with_mapping(
                metric_result, target_widget
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return WidgetExecutionResult(
                widget_alias=widget_alias,
                data=chart_data,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            raise WidgetExecutionError(widget_alias, str(e))
    
    @staticmethod
    def _execute_metric(widget, view) -> MetricExecutionResult:
        """
        Execute the metric for a widget.
        This is a simplified implementation - in production this would integrate
        with the actual metric execution service.
        
        Args:
            widget: The dashboard widget
            view: The dashboard view (for context)
            
        Returns:
            MetricExecutionResult: Mock metric execution result
        """
        # TODO: Integrate with actual metric execution service
        # For now, return mock data based on visualization type
        
        from cortex.core.types.dashboards import VisualizationType
        
        viz_type = widget.visualization.type
        
        if viz_type == VisualizationType.SINGLE_VALUE:
            return MetricExecutionResult(
                columns=["value"],
                data=[[42.5]],
                total_rows=1,
                execution_time_ms=50.0
            )
        elif viz_type in [VisualizationType.PIE_CHART, VisualizationType.DONUT_CHART]:
            return MetricExecutionResult(
                columns=["category", "value"],
                data=[
                    ["Product A", 100],
                    ["Product B", 150],
                    ["Product C", 75]
                ],
                total_rows=3,
                execution_time_ms=75.0
            )
        elif viz_type == VisualizationType.TABLE:
            return MetricExecutionResult(
                columns=["date", "product", "revenue"],
                data=[
                    ["2024-01-01", "Product A", 1000],
                    ["2024-01-01", "Product B", 1500],
                    ["2024-01-02", "Product A", 1200],
                    ["2024-01-02", "Product B", 1300]
                ],
                total_rows=4,
                execution_time_ms=100.0
            )
        else:
            # Default to series-based charts
            return MetricExecutionResult(
                columns=["date", "product", "revenue"],
                data=[
                    ["2024-01-01", "Product A", 1000],
                    ["2024-01-01", "Product B", 1500],
                    ["2024-01-02", "Product A", 1200],
                    ["2024-01-02", "Product B", 1300],
                    ["2024-01-03", "Product A", 1100],
                    ["2024-01-03", "Product B", 1600]
                ],
                total_rows=6,
                execution_time_ms=120.0
            )
    
    @staticmethod
    def _transform_with_mapping(metric_result: MetricExecutionResult, widget) -> StandardChartData:
        """
        Transform metric result using the widget's field mapping configuration.
        
        Args:
            metric_result: The result from metric execution
            widget: The dashboard widget with visualization and mapping config
            
        Returns:
            StandardChartData: Transformed data ready for visualization
        """
        try:
            # Convert metric result to list of dictionaries
            result_data = []
            for row in metric_result.data:
                row_dict = {}
                for i, column in enumerate(metric_result.columns):
                    row_dict[column] = row[i] if i < len(row) else None
                result_data.append(row_dict)
            
            # Create visualization mapping
            visualization_mapping = MappingFactory.create_mapping(
                visualization_type=widget.visualization.type,
                data_mapping=widget.visualization.data_mapping,
                visualization_config=widget.visualization.model_dump()
            )
            
            # Validate mapping against metric result columns
            visualization_mapping.validate(metric_result.columns)
            
            # Transform data using the mapping
            transformed_data = visualization_mapping.transform_data(result_data)
            
            # Convert to StandardChartData format
            return StandardChartData(
                raw={"columns": metric_result.columns, "data": metric_result.data},
                processed=transformed_data,
                metadata={
                    "execution_time_ms": metric_result.execution_time_ms,
                    "total_rows": metric_result.total_rows,
                    "visualization_type": widget.visualization.type.value,
                    "field_mappings": widget.visualization.data_mapping.model_dump(),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None
                }
            )
            
        except MappingValidationError as e:
            # Handle mapping validation errors gracefully
            return StandardChartData(
                raw={"columns": metric_result.columns, "data": metric_result.data},
                processed={"error": f"Mapping validation failed: {e.message}"},
                metadata={
                    "execution_time_ms": metric_result.execution_time_ms,
                    "total_rows": metric_result.total_rows,
                    "error": str(e),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None
                }
            )
        except Exception as e:
            # Handle other transformation errors
            return StandardChartData(
                raw={"columns": metric_result.columns, "data": metric_result.data},
                processed={"error": f"Data transformation failed: {str(e)}"},
                metadata={
                    "execution_time_ms": metric_result.execution_time_ms,
                    "total_rows": metric_result.total_rows,
                    "error": str(e),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None
                }
            )