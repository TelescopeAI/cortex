from typing import Optional, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.requests.dashboards import (
    DashboardCreateRequest, DashboardUpdateRequest, SetDefaultViewRequest
)
from cortex.api.schemas.responses.dashboards import (
    DashboardResponse, DashboardListResponse, DashboardExecutionResponse, DashboardViewExecutionResponse,
    WidgetExecutionResponse
)
from cortex.core.dashboards.dashboard import Dashboard
from cortex.core.dashboards.db.dashboard_service import DashboardCRUD
from cortex.core.dashboards.execution import DashboardExecutionService
from cortex.core.dashboards.mapping.base import DataMapping, FieldMapping, ColumnMapping
from cortex.core.dashboards.mapping.base import MappingValidationError
from cortex.core.dashboards.mapping.factory import MappingFactory
from cortex.core.dashboards.transformers import ProcessedChartData, ChartMetadata
from cortex.core.dashboards.transformers import StandardChartData
from cortex.core.exceptions.dashboards import (
    DashboardDoesNotExistError, DashboardAlreadyExistsError,
    DashboardViewDoesNotExistError, InvalidDefaultViewError,
    DashboardExecutionError, WidgetExecutionError
)
from cortex.core.services.metrics.execution import MetricExecutionService
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.types.dashboards import AxisDataType
from cortex.core.dashboards.transformers import MetricExecutionResult
from cortex.core.dashboards.dashboard import (
        DashboardView, DashboardSection, DashboardWidget,
        VisualizationConfig, DataMapping, WidgetGridConfig,
        DashboardLayout, MetricExecutionOverrides,
        SingleValueConfig, GaugeConfig, ChartConfig
    )

DashboardRouter = APIRouter()


@DashboardRouter.post(
    "/dashboards",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Dashboards"]
)
async def create_dashboard(dashboard_data: DashboardCreateRequest):
    """Create a new dashboard with views, sections, and widgets."""
    try:
        # Convert request to domain model
        dashboard = _convert_create_request_to_dashboard(dashboard_data)

        # Create dashboard
        created_dashboard = DashboardCRUD.add_dashboard(dashboard)

        return DashboardResponse(**created_dashboard.model_dump())
    except DashboardAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    # except Exception as e:
    #     print(str(e))
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=str(e)
    #     )


@DashboardRouter.get(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def get_dashboard(dashboard_id: UUID):
    """Get a dashboard by ID with all views, sections, and widgets."""
    try:
        dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if dashboard is None:
            raise DashboardDoesNotExistError(dashboard_id)

        return DashboardResponse(**dashboard.model_dump())
    except DashboardDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.get(
    "/environments/{environment_id}/dashboards",
    response_model=DashboardListResponse,
    tags=["Dashboards"]
)
async def get_dashboards_by_environment(environment_id: UUID):
    """Get all dashboards for a specific environment."""
    try:
        dashboards = DashboardCRUD.get_dashboards_by_environment(environment_id)

        return DashboardListResponse(
            dashboards=[DashboardResponse(**dashboard.model_dump()) for dashboard in dashboards],
            total=len(dashboards)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.put(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def update_dashboard(dashboard_id: UUID, dashboard_data: DashboardUpdateRequest):
    """Update dashboard metadata (name, description, type, tags)."""
    try:
        # Get existing dashboard
        existing_dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if existing_dashboard is None:
            raise DashboardDoesNotExistError(dashboard_id)

        # Update fields that are provided (metadata)
        if dashboard_data.alias is not None:
            existing_dashboard.alias = dashboard_data.alias
        if dashboard_data.name is not None:
            existing_dashboard.name = dashboard_data.name
        if dashboard_data.description is not None:
            existing_dashboard.description = dashboard_data.description
        if dashboard_data.type is not None:
            existing_dashboard.type = dashboard_data.type
        if dashboard_data.tags is not None:
            existing_dashboard.tags = dashboard_data.tags
        if dashboard_data.default_view is not None:
            existing_dashboard.default_view = dashboard_data.default_view

        # Update nested config if provided
        if dashboard_data.views is not None:
            # Rebuild views using the same conversion method as create
            temp_request = DashboardCreateRequest(
                environment_id=existing_dashboard.environment_id,
                name=existing_dashboard.name,
                description=existing_dashboard.description,
                type=existing_dashboard.type,
                views=dashboard_data.views,
                default_view_index=0,
                tags=existing_dashboard.tags,
                alias=existing_dashboard.alias,
            )
            updated_model = _convert_create_request_to_dashboard(temp_request)
        else:
            # If no views update, use existing dashboard as updated model
            updated_model = existing_dashboard

        # Merge strategy: preserve existing widget data_mapping fields when the incoming update omits them
        merged_views = []
        for new_view in updated_model.views:
            # find existing view by alias
            old_view = next((v for v in (existing_dashboard.views or []) if v.alias == new_view.alias), None)
            if not old_view:
                merged_views.append(new_view)
                continue
            merged_sections = []
            for new_sec in new_view.sections:
                old_sec = next((s for s in (old_view.sections or []) if s.alias == new_sec.alias), None)
                if not old_sec:
                    merged_sections.append(new_sec)
                    continue
                merged_widgets = []
                for new_w in new_sec.widgets:
                    old_w = None
                    for ow in (old_sec.widgets or []):
                        if ow.alias == new_w.alias:
                            old_w = ow
                            break
                    if not old_w:
                        merged_widgets.append(new_w)
                        continue
                    # Merge data_mapping conservatively
                    nm = new_w.visualization.data_mapping
                    om = old_w.visualization.data_mapping
                    # If y_axes missing/empty in update, preserve existing
                    if (not getattr(nm, 'y_axes', None)) and getattr(om, 'y_axes', None):
                        nm.y_axes = om.y_axes
                    # If x_axis missing but exists before, preserve
                    if (not getattr(nm, 'x_axis', None)) and getattr(om, 'x_axis', None):
                        nm.x_axis = om.x_axis
                    # Preserve series_field/value_field/category_field if omitted
                    if (not getattr(nm, 'series_field', None)) and getattr(om, 'series_field', None):
                        nm.series_field = om.series_field
                    if (not getattr(nm, 'value_field', None)) and getattr(om, 'value_field', None):
                        nm.value_field = om.value_field
                    if (not getattr(nm, 'category_field', None)) and getattr(om, 'category_field', None):
                        nm.category_field = om.category_field
                    # Preserve columns if omitted
                    if (not getattr(nm, 'columns', None)) and getattr(om, 'columns', None):
                        nm.columns = om.columns
                    
                    # Preserve chart_config if omitted
                    if (not getattr(new_w.visualization, 'chart_config', None)) and getattr(old_w.visualization, 'chart_config', None):
                        new_w.visualization.chart_config = old_w.visualization.chart_config
                    
                    merged_widgets.append(new_w)
                # carry over any widgets that were not present in update payload
                new_aliases = {w.alias for w in new_sec.widgets}
                for ow in (old_sec.widgets or []):
                    if ow.alias not in new_aliases:
                        merged_widgets.append(ow)
                new_sec.widgets = merged_widgets
                merged_sections.append(new_sec)
            # carry over any sections not present in update
            new_sec_aliases = {s.alias for s in new_view.sections}
            for os in (old_view.sections or []):
                if os.alias not in new_sec_aliases:
                    merged_sections.append(os)
            new_view.sections = merged_sections
            merged_views.append(new_view)

        existing_dashboard.views = merged_views

        # Update dashboard
        updated_dashboard = DashboardCRUD.update_dashboard(dashboard_id, existing_dashboard)

        return DashboardResponse(**updated_dashboard.model_dump())
    except DashboardDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.delete(
    "/dashboards/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dashboards"]
)
async def delete_dashboard(dashboard_id: UUID):
    """Delete a dashboard and all its related data."""
    try:
        success = DashboardCRUD.delete_dashboard(dashboard_id)
        if not success:
            raise DashboardDoesNotExistError(dashboard_id)
    except DashboardDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/default-view",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def set_default_view(dashboard_id: UUID, request: SetDefaultViewRequest):
    """Set the default view for a dashboard."""
    try:
        updated_dashboard = DashboardCRUD.set_default_view(dashboard_id, request.view_alias)

        return DashboardResponse(**updated_dashboard.model_dump())
    except (DashboardDoesNotExistError, InvalidDefaultViewError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Dashboard execution endpoints
@DashboardRouter.post(
    "/dashboards/{dashboard_id}/execute",
    response_model=DashboardExecutionResponse,
    tags=["Dashboards"]
)
async def execute_dashboard(dashboard_id: UUID, view_alias: Optional[str] = None):
    """Execute a dashboard (or specific view) and return chart data for all widgets."""
    try:
        execution_result = DashboardExecutionService.execute_dashboard(dashboard_id, view_alias)

        return DashboardExecutionResponse(**execution_result.model_dump())
    except DashboardDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DashboardExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/views/{view_alias}/execute",
    response_model=DashboardViewExecutionResponse,
    tags=["Dashboards"]
)
async def execute_dashboard_view(dashboard_id: UUID, view_alias: str):
    """Execute a specific dashboard view and return chart data for all widgets."""
    try:
        execution_result = DashboardExecutionService.execute_view(dashboard_id, view_alias)

        return DashboardViewExecutionResponse(**execution_result.model_dump())
    except (DashboardDoesNotExistError, DashboardViewDoesNotExistError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DashboardExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/views/{view_alias}/widgets/{widget_alias}/execute",
    response_model=WidgetExecutionResponse,
    tags=["Dashboards"]
)
async def execute_widget(dashboard_id: UUID, view_alias: str, widget_alias: str):
    """Execute a specific widget and return its chart data.

    This mirrors the preview behavior, but loads the persisted dashboard config
    and executes the real metric for the widget.
    """
    try:
        # Load dashboard
        dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if dashboard is None:
            raise DashboardDoesNotExistError(dashboard_id)

        # Find view
        target_view = None
        for v in dashboard.views:
            if v.alias == view_alias:
                target_view = v
                break
        if target_view is None:
            raise DashboardViewDoesNotExistError(view_alias)

        # Find widget by alias across sections
        target_widget = None
        for s in target_view.sections:
            for w in s.widgets:
                if w.alias == widget_alias:
                    target_widget = w
                    break
            if target_widget:
                break
        if target_widget is None:
            raise WidgetExecutionError(widget_alias, "Widget not found")

        # Execute metric using shared service - support both metric_id and embedded metric
        execution_kwargs = {
            "context_id": target_view.context_id
        }
        
        if target_widget.metric:
            # Use embedded metric
            execution_kwargs["metric"] = target_widget.metric
        elif target_widget.metric_id:
            # Use metric reference
            execution_kwargs["metric_id"] = target_widget.metric_id
        else:
            raise WidgetExecutionError(widget_alias, "Widget must have either metric_id or embedded metric")

        execution_result = MetricExecutionService.execute_metric(**execution_kwargs)

        if not execution_result.get("success"):
            data_payload = _create_error_chart_data(execution_result.get("error", "Metric execution failed"))
            return WidgetExecutionResponse(
                widget_alias=widget_alias,
                data=data_payload,
                execution_time_ms=execution_result.get("metadata", {}).get("execution_time_ms", 0.0),
                error=execution_result.get("error")
            )

        metric_result = _convert_to_metric_execution_result(execution_result)

        # Transform data using the same mapper as preview
        transformed_data = _transform_widget_data_with_mapping(target_widget, metric_result)

        return WidgetExecutionResponse(
            widget_alias=widget_alias,
            data=transformed_data,
            execution_time_ms=execution_result.get("metadata", {}).get("execution_time_ms", 0.0),
            error=None
        )
    except (DashboardDoesNotExistError, DashboardViewDoesNotExistError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WidgetExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@DashboardRouter.delete(
    "/dashboards/{dashboard_id}/views/{view_alias}/widgets/{widget_alias}",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def delete_widget(dashboard_id: UUID, view_alias: str, widget_alias: str):
    """Delete a specific widget from a dashboard view.
    
    Returns the updated dashboard configuration after widget removal.
    """
    try:
        # Load dashboard
        dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if dashboard is None:
            raise DashboardDoesNotExistError(dashboard_id)

        # Find view
        target_view = None
        view_index = None
        for i, v in enumerate(dashboard.views):
            if v.alias == view_alias:
                target_view = v
                view_index = i
                break
        if target_view is None:
            raise DashboardViewDoesNotExistError(view_alias)

        # Find widget by alias across sections and remove it
        widget_found = False
        for section in target_view.sections:
            for widget_index, widget in enumerate(section.widgets):
                if widget.alias == widget_alias:
                    section.widgets.pop(widget_index)
                    widget_found = True
                    break
            if widget_found:
                break
        
        if not widget_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Widget '{widget_alias}' not found in view '{view_alias}'"
            )

        # Update dashboard in database
        updated_dashboard = DashboardCRUD.update_dashboard(dashboard_id, dashboard)
        
        return DashboardResponse.model_validate(updated_dashboard, from_attributes=True)
        
    except DashboardDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DashboardViewDoesNotExistError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Helper functions
def _convert_create_request_to_dashboard(request: DashboardCreateRequest) -> Dashboard:
    """Convert dashboard create request to domain model."""
    
    # Convert views (support optional aliases in future; client can send in layout field later)
    views = []
    default_view_id = None

    for i, view_req in enumerate(request.views):
        # Convert sections
        sections = []
        for section_req in view_req.sections:
            # Convert widgets
            widgets = []
            for widget_req in section_req.widgets:
                # Build a robust DataMapping directly from FieldMappingRequest
                dm_req = widget_req.visualization.data_mapping

                def _fm(m, default: str, required_default: bool = False):
                    if not m:
                        return None
                    return FieldMapping(
                        field=m.field,
                        data_type=(m.data_type or default),
                        label=getattr(m, 'label', None),
                        required=bool(getattr(m, 'required', required_default)),
                    )

                data_mapping = DataMapping(
                    x_axis=_fm(getattr(dm_req, 'x_axis', None), 'categorical', False),
                    y_axes=[_fm(ym, 'numerical', True) for ym in (getattr(dm_req, 'y_axes', None) or [])] or None,
                    series_field=_fm(getattr(dm_req, 'series_field', None), 'categorical', False),
                    columns=[
                        {
                            'field': getattr(col, 'field', None) or (col.get('field') if isinstance(col, dict) else None),
                            'label': getattr(col, 'label', None) or (col.get('label') if isinstance(col, dict) else None),
                            'width': getattr(col, 'width', None) if not isinstance(col, dict) else col.get('width'),
                            'sortable': getattr(col, 'sortable', None) if not isinstance(col, dict) else col.get('sortable'),
                            'filterable': getattr(col, 'filterable', None) if not isinstance(col, dict) else col.get('filterable'),
                            'alignment': getattr(col, 'alignment', None) if not isinstance(col, dict) else col.get('alignment'),
                        }
                        for col in (getattr(dm_req, 'columns', None) or [])
                    ] or None,
                )

                # Convert visualization config
                viz_config = VisualizationConfig(
                    type=widget_req.visualization.type,
                    data_mapping=data_mapping,
                    chart_config=(
                        ChartConfig(**widget_req.visualization.chart_config.model_dump(exclude_none=True))
                        if widget_req.visualization.chart_config else None
                    ),
                    single_value_config=(
                        SingleValueConfig(**widget_req.visualization.single_value_config.model_dump(exclude_none=True))
                        if widget_req.visualization.single_value_config else None
                    ),
                    gauge_config=(
                        GaugeConfig(**widget_req.visualization.gauge_config.model_dump(exclude_none=True))
                        if widget_req.visualization.gauge_config else None
                    ),
                    show_legend=widget_req.visualization.show_legend,
                    show_grid=widget_req.visualization.show_grid,
                    show_axes_labels=widget_req.visualization.show_axes_labels,
                    color_scheme=widget_req.visualization.color_scheme,
                    custom_colors=widget_req.visualization.custom_colors
                )

                # Handle both metric_id (reference) and metric (embedded)
                widget_kwargs = {
                    "alias": widget_req.alias,
                    "section_alias": widget_req.section_alias,
                    "position": widget_req.position,
                    "grid_config": WidgetGridConfig(**widget_req.grid_config.model_dump()),
                    "title": widget_req.title,
                    "description": widget_req.description,
                    "visualization": viz_config,
                    "metric_overrides": MetricExecutionOverrides(
                        **widget_req.metric_overrides.model_dump()) if widget_req.metric_overrides else None
                }
                
                # Add metric_id or metric, whichever is provided
                if widget_req.metric:
                    # Convert MetricCreateRequest to SemanticMetric for embedded metric
                    
                    widget_kwargs["metric"] = SemanticMetric(
                        id=uuid4(),  # Generate temporary ID for embedded metric
                        environment_id=request.environment_id,
                        **widget_req.metric.model_dump()
                    )
                elif widget_req.metric_id:
                    widget_kwargs["metric_id"] = widget_req.metric_id
                
                widget = DashboardWidget(**widget_kwargs)
                widgets.append(widget)

            section = DashboardSection(
                alias=section_req.alias,
                title=section_req.title,
                description=section_req.description,
                position=section_req.position,
                widgets=widgets
            )
            sections.append(section)

        view = DashboardView(
            alias=view_req.alias,
            title=view_req.title,
            description=view_req.description,
            sections=sections,
            context_id=view_req.context_id,
            layout=DashboardLayout(**view_req.layout.model_dump()) if view_req.layout else None
        )
        views.append(view)

        # Set default view
        if i == request.default_view_index:
            default_view_id = view.alias

    # If no default set, use first view
    if default_view_id is None and views:
        default_view_id = views[0].alias

    dashboard = Dashboard(
        id=uuid4(),
        environment_id=request.environment_id,
        alias=request.alias,
        name=request.name,
        description=request.description,
        type=request.type,
        views=views,
        default_view=default_view_id,
        tags=request.tags,
        created_by=uuid4()  # TODO: Get from auth context
    )

    # Views no longer need dashboard_id reference since they're embedded in the dashboard

    return dashboard


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/preview",
    response_model=DashboardExecutionResponse,
    tags=["Dashboards"]
)
async def preview_dashboard(dashboard_id: UUID, config: DashboardUpdateRequest):
    """
    Preview dashboard execution results without saving to database.
    Takes a dashboard configuration and simulates execution to show expected output.
    """
    try:
        # Validate the configuration structure
        if not config.views or len(config.views) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dashboard must have at least one view for preview"
            )

        # Use the first view for preview (or could be made configurable)
        preview_view = config.views[0]

        # Simulate metric execution and mapping transformation
        preview_results = []

        for section in preview_view.sections:
            for index, widget in enumerate(section.widgets):
                try:
                    # Execute the actual metric - support both metric_id and embedded metric
                    execution_kwargs = {
                        "context_id": preview_view.context_id
                    }
                    
                    if widget.metric:
                        # Convert MetricCreateRequest to SemanticMetric for execution
                        embedded_metric = SemanticMetric(
                            id=uuid4(),  # Generate temporary ID
                            environment_id=config.environment_id if hasattr(config, 'environment_id') else uuid4(),
                            **widget.metric.model_dump()
                        )
                        execution_kwargs["metric"] = embedded_metric
                    elif widget.metric_id:
                        execution_kwargs["metric_id"] = widget.metric_id
                    else:
                        raise ValueError("Widget must have either metric_id or embedded metric for preview")

                    # Execute metric using the shared service
                    execution_result = MetricExecutionService.execute_metric(**execution_kwargs)

                    if not execution_result.get("success"):
                        raise Exception(execution_result.get("error", "Metric execution failed"))

                    # Convert to metric execution result format for mapping
                    metric_result = _convert_to_metric_execution_result(execution_result)

                    # Apply field mapping transformation
                    transformed_data = _transform_widget_data_with_mapping(widget, metric_result)

                    preview_results.append({
                        "widget_alias": widget.alias if hasattr(widget, 'alias') else f"preview_widget_{index}",
                        "data": transformed_data,
                        "execution_time_ms": execution_result.get("metadata", {}).get("execution_time_ms", 0.0),
                        "error": None
                    })

                except MappingValidationError as e:
                    preview_results.append({
                        "widget_alias": widget.alias if hasattr(widget, 'alias') else f"preview_widget_{index}",
                        "data": _create_error_chart_data(f"Mapping validation failed: {e.message}"),
                        "execution_time_ms": 0.0,
                        "error": str(e)
                    })
                except Exception as e:
                    preview_results.append({
                        "widget_alias": widget.alias if hasattr(widget, 'alias') else f"preview_widget_{index}",
                        "data": _create_error_chart_data(f"Preview generation failed: {str(e)}"),
                        "execution_time_ms": 0.0,
                        "error": str(e)
                    })

        # Return preview result in execution response format
        return DashboardExecutionResponse(
            dashboard_id=dashboard_id,
            view_alias="preview_view",
            view_execution={
                "view_alias": "preview_view",
                "widgets": preview_results,
                "total_execution_time_ms": sum(w.get("execution_time_ms", 0) for w in preview_results),
                "errors": [w.get("error") for w in preview_results if w.get("error")]
            },
            total_execution_time_ms=sum(w.get("execution_time_ms", 0) for w in preview_results)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )


def _create_error_chart_data(error_message: str):
    """Create a StandardChartData object for error cases with all required fields."""

    # Build a valid structure matching transformers' models exactly
    processed = ProcessedChartData()
    metadata = ChartMetadata(
        title="Error",
        description=error_message,
        x_axis_title="",
        y_axes_title="",
        data_types={},
        formatting={},
        ranges={}
    )

    return StandardChartData(
        raw={"columns": [], "data": []},
        processed=processed,
        metadata=metadata,
    ).model_dump()


def _convert_to_metric_execution_result(execution_result):
    """Convert metric service execution result to MetricExecutionResult format."""


    # Extract data from the execution result
    data = execution_result.get("data", [])
    metadata = execution_result.get("metadata", {})

    # Determine columns - try to get from metadata or infer from first row
    columns = metadata.get("columns", [])
    if not columns and data:
        # If no columns in metadata, try to infer from first row if it's a dict
        first_row = data[0] if data else {}
        if isinstance(first_row, dict):
            columns = list(first_row.keys())
        else:
            # Fallback: generate generic column names
            columns = [f"col_{i}" for i in range(len(first_row) if first_row else 0)]

    # Convert data to list of lists format if needed
    if data and isinstance(data[0], dict):
        # Convert from list of dicts to list of lists
        converted_data = []
        for row in data:
            converted_data.append([row.get(col) for col in columns])
        data = converted_data

    return MetricExecutionResult(
        columns=columns,
        data=data,
        total_rows=len(data),
        execution_time_ms=metadata.get("execution_time_ms", 0.0)
    )


def _transform_widget_data_with_mapping(widget, metric_result):
    """Transform widget data using field mapping, similar to execution service."""

    def _normalize_axis_type(value: Optional[str], default: str) -> str:
        """Normalize loosely provided axis data types to valid enum values."""
        if not value:
            return default
        v = str(value).strip().lower()
        if v in {"categorical", "category"}:
            return "categorical"
        if v in {"numerical", "numeric", "number"}:
            return "numerical"
        if v in {"temporal", "time", "date", "datetime"}:
            return "temporal"
        # Fallback
        return default

    try:
        # Convert metric result to list of dictionaries
        result_data = []
        for row in metric_result.data:
            row_dict = {}
            for i, column in enumerate(metric_result.columns):
                row_dict[column] = row[i] if i < len(row) else None
            result_data.append(row_dict)


        # Convert request data mapping (AxisMapping in domain) to FieldMapping used by transformers
        request_mapping = widget.visualization.data_mapping

        def _mapping_type(m: Any, default: str) -> str:
            # Accept either AxisMapping.type or FieldMapping.data_type
            # Prefer explicit request data_type; if missing, attempt to infer from metric result columns suffixes
            inferred = getattr(m, 'data_type', None) or getattr(m, 'type', None)
            return _normalize_axis_type(inferred, default)

        def _to_field_mapping(m: Any, default: str, required_default: bool = False, force_numeric: bool = False) -> Optional[FieldMapping]:
            if not m:
                return None
            dtype = _mapping_type(m, default)
            if force_numeric:
                dtype = 'numerical'
            return FieldMapping(
                field=getattr(m, 'field', None),
                data_type=dtype,
                label=getattr(m, 'label', None),
                required=bool(getattr(m, 'required', required_default)),
            )

        # Build DataMapping expected by mapping engine
        domain_data_mapping = DataMapping(
            x_axis=_to_field_mapping(getattr(request_mapping, 'x_axis', None), 'categorical', False),
            y_axes=[
                _to_field_mapping(ym, 'numerical', True, True)
                for ym in (getattr(request_mapping, 'y_axes', None) or [])
            ] or None,
            # Legacy/category-value support (may not be present on domain model)
            value_field=_to_field_mapping(getattr(request_mapping, 'value_field', None), 'numerical', True),
            category_field=_to_field_mapping(getattr(request_mapping, 'category_field', None), 'categorical', True),
            # Accept both series_field and series_by from domain
            series_field=_to_field_mapping(
                getattr(request_mapping, 'series_field', None) or getattr(request_mapping, 'series_by', None),
                'categorical',
                False,
            ),
            columns=[
                ColumnMapping(
                    field=getattr(col, 'field', None) or (col.get('field') if isinstance(col, dict) else None),
                    label=(getattr(col, 'label', None) or (col.get('label') if isinstance(col, dict) else None) or (getattr(col, 'field', None) if hasattr(col, 'field') else None)),
                    width=getattr(col, 'width', None) if not isinstance(col, dict) else col.get('width'),
                    sortable=(getattr(col, 'sortable', False) if not isinstance(col, dict) else bool(col.get('sortable', False))),
                    filterable=(getattr(col, 'filterable', False) if not isinstance(col, dict) else bool(col.get('filterable', False))),
                    alignment=getattr(col, 'alignment', None) if not isinstance(col, dict) else col.get('alignment'),
                ) for col in (getattr(request_mapping, 'columns', None) or [])
            ] or None,
        )

        # If there is no data or columns, return a safe default preview without failing
        if not metric_result.columns or not metric_result.data:
            safe_processed = {
                "series": None,
                "categories": None,
                "table": None,
            }
            if widget.visualization.type.value in ("single_value", "gauge"):
                safe_processed["value"] = 0
            transformed_data = safe_processed
        else:
            # Create visualization mapping using domain model
            visualization_mapping = MappingFactory.create_mapping(
                visualization_type=widget.visualization.type,
                data_mapping=domain_data_mapping,
                visualization_config=widget.visualization.model_dump()
            )

            # For single_value visualization, value_field is sufficient; skip strict XY validation
            if getattr(widget.visualization.type, 'value', widget.visualization.type) == 'single_value':
                # Validate only the fields that exist in the result
                try:
                    required_cols = [domain_data_mapping.value_field.field] if domain_data_mapping.value_field else []
                    for col in required_cols:
                        if col not in metric_result.columns:
                            raise MappingValidationError(col, f"Field '{col}' not found in metric result columns: {metric_result.columns}")
                except Exception:
                    pass
            else:
                # Validate mapping against metric result columns for chart types
                # If y_axes have missing or ambiguous data_type, infer as numerical
                for ym in (domain_data_mapping.y_axes or []):
                    if not getattr(ym, 'data_type', None):
                        ym.data_type = AxisDataType.NUMERICAL
                visualization_mapping.validate(metric_result.columns)

            # Transform data using the mapping
            transformed_data = visualization_mapping.transform_data(result_data)

        # Resolve normalized data types for metadata (use normalized/domain values)
        x_type = None
        y_type = None
        try:
            if domain_data_mapping.x_axis:
                x_type = getattr(domain_data_mapping.x_axis.data_type, 'value', domain_data_mapping.x_axis.data_type)
            if domain_data_mapping.y_axes and len(domain_data_mapping.y_axes) > 0:
                y_type = getattr(domain_data_mapping.y_axes[0].data_type, 'value', domain_data_mapping.y_axes[0].data_type)
        except Exception:
            pass
        # Fallback to request mapping (supports both .data_type and .type)
        x_src = getattr(request_mapping, 'x_axis', None)
        x_type = x_type or _normalize_axis_type((getattr(x_src, 'data_type', None) or getattr(x_src, 'type', None)), 'categorical')
        if not y_type and getattr(request_mapping, 'y_axes', None):
            first_y = request_mapping.y_axes[0]
            y_type = _normalize_axis_type((getattr(first_y, 'data_type', None) or getattr(first_y, 'type', None)), 'numerical')

        # Build metadata types/title conditionally to avoid None enums for single-value/gauge
        _data_types = {}
        if x_type:
            _data_types["x_axis"] = x_type
        if y_type:
            _data_types["y_axes"] = y_type

        y_title = ""
        if getattr(request_mapping, 'y_axes', None) and request_mapping.y_axes:
            first_y = request_mapping.y_axes[0]
            if getattr(first_y, 'label', None):
                y_title = first_y.label

        # Convert to StandardChartData format with all required metadata
        # Safely resolve axis titles even when request mapping is AxisMapping without 'label'
        x_axis_label = "X Axis"
        try:
            if getattr(request_mapping, 'x_axis', None):
                x_label_candidate = getattr(request_mapping.x_axis, 'label', None)
                if x_label_candidate:
                    x_axis_label = x_label_candidate
        except Exception:
            pass

        return StandardChartData(
            raw={"columns": metric_result.columns, "data": metric_result.data},
            processed=transformed_data,
            metadata=ChartMetadata(
                title=(widget.title if hasattr(widget, 'title') else "Preview Widget"),
                description=(widget.description if hasattr(widget, 'description') else ""),
                x_axis_title=x_axis_label,
                y_axes_title=y_title,
                data_types=_data_types,
                formatting={},
                ranges={},
            )
        ).model_dump()

    except Exception as e:
        # Always return a valid StandardChartData payload, even on errors
        return _create_error_chart_data(f"Data transformation failed: {str(e)}")
