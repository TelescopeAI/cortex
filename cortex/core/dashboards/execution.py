import time
from typing import Optional, List
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.exceptions.dashboards import (
    DashboardDoesNotExistError, DashboardViewDoesNotExistError,
    DashboardWidgetDoesNotExistError, DashboardExecutionError, WidgetExecutionError
)
from cortex.core.dashboards.db.dashboard_service import DashboardCRUD
from cortex.core.dashboards.transformers import (
    StandardChartData
)
from cortex.core.dashboards.mapping.factory import MappingFactory
from cortex.core.dashboards.mapping.base import MappingValidationError
from cortex.core.services.metrics.execution import MetricExecutionService



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
            
            # Execute the metric and transform data
            chart_data = DashboardExecutionService._execute_metric(
                target_widget, target_view
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
    def _execute_metric(widget, view) -> StandardChartData:
        """
        Execute the metric for a widget and transform using field mapping.
        
        Args:
            widget: The dashboard widget (with either metric_id or metric)
            view: The dashboard view (for context)
            
        Returns:
            StandardChartData: Transformed data ready for visualization
        """
        
        start_time = time.time()
        
        # Build execution kwargs - support both metric_id and embedded metric
        execution_kwargs = {
            "context_id": view.context_id if hasattr(view, 'context_id') else None,
            "parameters": widget.metric_overrides.get('parameters') if widget.metric_overrides else None,
            "limit": widget.metric_overrides.get('limit') if widget.metric_overrides else None,
        }
        
        if widget.metric is not None:
            # Use embedded metric directly
            execution_kwargs["metric"] = widget.metric
        else:
            # Use metric_id reference
            execution_kwargs["metric_id"] = widget.metric_id
        
        # Execute the metric using the actual metric execution service
        execution_result = MetricExecutionService.execute_metric(**execution_kwargs)
        
        # Handle execution failure
        if not execution_result.get("success"):
            error_msg = execution_result.get("error", "Metric execution failed")
            return StandardChartData(
                raw={},
                processed={"error": error_msg},
                metadata={
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "error": error_msg,
                    "visualization_type": widget.visualization.type.value,
                }
            )
        
        # Extract data and metadata
        result_data = execution_result.get("data", [])
        metadata = execution_result.get("metadata", {})
        execution_time_ms = metadata.get("duration", (time.time() - start_time) * 1000)
        row_count = metadata.get("row_count", len(result_data) if result_data else 0)
        
        # Extract column names from the first row (data is already in dict format)
        columns = list(result_data[0].keys()) if result_data else []
        
        # Transform metric result using field mapping
        try:
            # Create visualization mapping
            visualization_mapping = MappingFactory.create_mapping(
                visualization_type=widget.visualization.type,
                data_mapping=widget.visualization.data_mapping,
                visualization_config=widget.visualization.model_dump()
            )
            
            # Validate mapping against metric result columns
            visualization_mapping.validate(columns)
            
            # Transform data using the mapping
            transformed_data = visualization_mapping.transform_data(result_data)
            
            # Convert to StandardChartData format
            return StandardChartData(
                raw={"columns": columns, "data": result_data},
                processed=transformed_data,
                metadata={
                    "execution_time_ms": execution_time_ms,
                    "total_rows": row_count,
                    "visualization_type": widget.visualization.type.value,
                    "field_mappings": widget.visualization.data_mapping.model_dump(),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None,
                    "query": metadata.get("query")
                }
            )
            
        except MappingValidationError as e:
            # Handle mapping validation errors gracefully
            return StandardChartData(
                raw={"columns": columns, "data": result_data},
                processed={"error": f"Mapping validation failed: {e.message}"},
                metadata={
                    "execution_time_ms": execution_time_ms,
                    "total_rows": row_count,
                    "error": str(e),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None
                }
            )
        except Exception as e:
            # Handle other transformation errors
            return StandardChartData(
                raw={"columns": columns, "data": result_data},
                processed={"error": f"Data transformation failed: {str(e)}"},
                metadata={
                    "execution_time_ms": execution_time_ms,
                    "total_rows": row_count,
                    "error": str(e),
                    "chart_config": widget.visualization.chart_config.model_dump() if widget.visualization.chart_config else None
                }
            )