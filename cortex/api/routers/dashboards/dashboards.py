from typing import Optional
from uuid import UUID

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
from cortex.core.services.metrics import MetricExecutionService

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
            existing_dashboard.views = updated_model.views

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
    """Execute a specific widget and return its chart data."""
    try:
        execution_result = DashboardExecutionService.execute_widget(dashboard_id, view_alias, widget_alias)

        return WidgetExecutionResponse(**execution_result.model_dump())
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


# Helper functions
def _convert_create_request_to_dashboard(request: DashboardCreateRequest) -> Dashboard:
    """Convert dashboard create request to domain model."""
    from cortex.core.dashboards.dashboard import (
        DashboardView, DashboardSection, DashboardWidget,
        VisualizationConfig, DataMapping, WidgetGridConfig,
        DashboardLayout, MetricExecutionOverrides,
        SingleValueConfig, GaugeConfig
    )
    from uuid import uuid4

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
                # Convert visualization config
                viz_config = VisualizationConfig(
                    type=widget_req.visualization.type,
                    data_mapping=DataMapping(**widget_req.visualization.data_mapping.model_dump()),
                    single_value_config=SingleValueConfig(
                        **widget_req.visualization.single_value_config.model_dump()) if widget_req.visualization.single_value_config else None,
                    gauge_config=GaugeConfig(
                        **widget_req.visualization.gauge_config.model_dump()) if widget_req.visualization.gauge_config else None,
                    show_legend=widget_req.visualization.show_legend,
                    show_grid=widget_req.visualization.show_grid,
                    show_axes_labels=widget_req.visualization.show_axes_labels,
                    color_scheme=widget_req.visualization.color_scheme,
                    custom_colors=widget_req.visualization.custom_colors
                )

                widget = DashboardWidget(
                    alias=widget_req.alias,
                    section_alias=widget_req.section_alias,
                    metric_id=widget_req.metric_id,
                    position=widget_req.position,
                    grid_config=WidgetGridConfig(**widget_req.grid_config.model_dump()),
                    title=widget_req.title,
                    description=widget_req.description,
                    visualization=viz_config,
                    metric_overrides=MetricExecutionOverrides(
                        **widget_req.metric_overrides.model_dump()) if widget_req.metric_overrides else None
                )
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
async def preview_dashboard_config(dashboard_id: UUID, config: DashboardUpdateRequest):
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
                    # Execute the actual metric
                    if not widget.metric_id:
                        raise ValueError("Widget must have a metric_id for preview")

                    # Execute metric using the shared service
                    execution_result = MetricExecutionService.execute_metric(
                        metric_id=widget.metric_id,
                        context_id=preview_view.context_id,
                        limit=100  # Limit preview results for performance
                    )

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
        y_axis_title="",
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
    from cortex.core.dashboards.transformers import MetricExecutionResult

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

        # Convert request data mapping to domain model
        request_mapping = widget.visualization.data_mapping

        # Create domain model data mapping
        domain_data_mapping = DataMapping(
            x_axis=FieldMapping(
                field=request_mapping.x_axis.field,
                data_type=_normalize_axis_type(request_mapping.x_axis.data_type, "categorical"),
                label=request_mapping.x_axis.label,
                required=(request_mapping.x_axis.required or False)
            ) if request_mapping.x_axis else None,
            y_axis=FieldMapping(
                field=request_mapping.y_axis.field,
                data_type=_normalize_axis_type(request_mapping.y_axis.data_type, "numerical"),
                label=request_mapping.y_axis.label,
                required=(request_mapping.y_axis.required or False)
            ) if request_mapping.y_axis else None,
            value_field=FieldMapping(
                field=request_mapping.value_field.field,
                data_type=_normalize_axis_type(request_mapping.value_field.data_type, "numerical"),
                label=request_mapping.value_field.label,
                required=(request_mapping.value_field.required or False)
            ) if request_mapping.value_field else None,
            category_field=FieldMapping(
                field=request_mapping.category_field.field,
                data_type=_normalize_axis_type(request_mapping.category_field.data_type, "categorical"),
                label=request_mapping.category_field.label,
                required=(request_mapping.category_field.required or False)
            ) if request_mapping.category_field else None,
            series_field=FieldMapping(
                field=request_mapping.series_field.field,
                data_type=_normalize_axis_type(request_mapping.series_field.data_type, "categorical"),
                label=request_mapping.series_field.label,
                required=(request_mapping.series_field.required or False)
            ) if request_mapping.series_field else None,
            columns=[
                ColumnMapping(
                    field=col.field,
                    label=col.label or col.field,
                    width=col.width,
                    sortable=col.sortable or False,
                    filterable=col.filterable or False,
                    alignment=col.alignment
                ) for col in request_mapping.columns
            ] if request_mapping.columns else None
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
                visualization_mapping.validate(metric_result.columns)

            # Transform data using the mapping
            transformed_data = visualization_mapping.transform_data(result_data)

        # Resolve normalized data types for metadata (use normalized/domain values)
        x_type = None
        y_type = None
        try:
            if domain_data_mapping.x_axis:
                x_type = getattr(domain_data_mapping.x_axis.data_type, 'value', domain_data_mapping.x_axis.data_type)
            if domain_data_mapping.y_axis:
                y_type = getattr(domain_data_mapping.y_axis.data_type, 'value', domain_data_mapping.y_axis.data_type)
        except Exception:
            pass
        x_type = x_type or _normalize_axis_type(getattr(request_mapping.x_axis, 'data_type', None), 'categorical')
        y_type = y_type or _normalize_axis_type(getattr(request_mapping.y_axis, 'data_type', None), 'numerical')

        # Convert to StandardChartData format with all required metadata
        return StandardChartData(
            raw={"columns": metric_result.columns, "data": metric_result.data},
            processed=transformed_data,
            metadata={
                "execution_time_ms": metric_result.execution_time_ms,
                "total_rows": metric_result.total_rows,
                "visualization_type": widget.visualization.type.value,
                "field_mappings": request_mapping.model_dump(),
                "preview_mode": True,
                "title": widget.title if hasattr(widget, 'title') else "Preview Widget",
                "description": widget.description if hasattr(widget, 'description') else "",
                "x_axis_title": (
                    request_mapping.x_axis.label if request_mapping.x_axis and request_mapping.x_axis.label else "X Axis"),
                "y_axis_title": (
                    request_mapping.y_axis.label if request_mapping.y_axis and request_mapping.y_axis.label else "Y Axis"),
                "data_types": {"x_axis": x_type, "y_axis": y_type},
                "formatting": {},
                "ranges": {}
            }
        ).model_dump()

    except Exception as e:
        # Always return a valid StandardChartData payload, even on errors
        return _create_error_chart_data(f"Data transformation failed: {str(e)}")
