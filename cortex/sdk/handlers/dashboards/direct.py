"""
Dashboards direct handler - Core service calls.

Handles dashboard operations in Direct mode.
"""
from typing import Optional
from uuid import UUID, uuid4

from cortex.core.dashboards.dashboard import Dashboard, DashboardView, DashboardSection, DashboardWidget
from cortex.core.dashboards.dashboard import VisualizationConfig, DataMapping, WidgetGridConfig
from cortex.core.dashboards.dashboard import DashboardLayout, MetricExecutionOverrides
from cortex.core.dashboards.dashboard import SingleValueConfig, GaugeConfig, ChartConfig
from cortex.core.dashboards.mapping.base import FieldMapping
from cortex.core.dashboards.db.dashboard_service import DashboardCRUD
from cortex.core.dashboards.execution import DashboardExecutionService
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.sdk.schemas.requests.dashboards import (
    DashboardCreateRequest,
    DashboardUpdateRequest,
    SetDefaultViewRequest
)
from cortex.sdk.schemas.responses.dashboards import (
    DashboardResponse,
    DashboardListResponse,
    DashboardExecutionResponse,
    DashboardViewExecutionResponse,
    WidgetExecutionResponse
)
from cortex.sdk.exceptions.mappers import CoreExceptionMapper
from cortex.sdk.exceptions.base import CortexNotFoundError


def create_dashboard(request: DashboardCreateRequest) -> DashboardResponse:
    """
    Create a new dashboard - direct Core service call.

    Args:
        request: Dashboard creation request

    Returns:
        Created dashboard response
    """
    try:
        # Convert request to domain model
        dashboard = _convert_create_request_to_dashboard(request)

        # Create dashboard
        created_dashboard = DashboardCRUD.add_dashboard(dashboard)

        return DashboardResponse(**created_dashboard.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def get_dashboard(dashboard_id: UUID) -> DashboardResponse:
    """
    Get a dashboard by ID - direct Core service call.

    Args:
        dashboard_id: Dashboard ID

    Returns:
        Dashboard response
    """
    try:
        dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if dashboard is None:
            raise CortexNotFoundError(f"Dashboard with ID {dashboard_id} not found")

        return DashboardResponse(**dashboard.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def list_dashboards(environment_id: UUID) -> DashboardListResponse:
    """
    List dashboards by environment - direct Core service call.

    Args:
        environment_id: Environment ID

    Returns:
        List of dashboard responses
    """
    try:
        dashboards = DashboardCRUD.get_dashboards_by_environment(environment_id)

        return DashboardListResponse(
            dashboards=[DashboardResponse(**dashboard.model_dump()) for dashboard in dashboards],
            total=len(dashboards)
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def update_dashboard(
    dashboard_id: UUID,
    request: DashboardUpdateRequest
) -> DashboardResponse:
    """
    Update a dashboard - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        request: Update request

    Returns:
        Updated dashboard response
    """
    try:
        # Get existing dashboard
        existing_dashboard = DashboardCRUD.get_dashboard_by_id(dashboard_id)
        if existing_dashboard is None:
            raise CortexNotFoundError(f"Dashboard with ID {dashboard_id} not found")

        # Update fields that are provided (metadata)
        if request.alias is not None:
            existing_dashboard.alias = request.alias
        if request.name is not None:
            existing_dashboard.name = request.name
        if request.description is not None:
            existing_dashboard.description = request.description
        if request.type is not None:
            existing_dashboard.type = request.type
        if request.tags is not None:
            existing_dashboard.tags = request.tags
        if request.default_view is not None:
            existing_dashboard.default_view = request.default_view

        # Update nested config if provided
        if request.views is not None:
            # Rebuild views using the same conversion method as create
            # Convert DashboardViewRequest instances to dicts for Pydantic validation
            temp_request = DashboardCreateRequest(
                environment_id=existing_dashboard.environment_id,
                name=existing_dashboard.name,
                description=existing_dashboard.description,
                type=existing_dashboard.type,
                views=[view.model_dump() for view in request.views],
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
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_dashboard(dashboard_id: UUID) -> None:
    """
    Delete a dashboard - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
    """
    try:
        success = DashboardCRUD.delete_dashboard(dashboard_id)
        if not success:
            raise CortexNotFoundError(f"Dashboard with ID {dashboard_id} not found")
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def set_default_view(dashboard_id: UUID, request: SetDefaultViewRequest) -> DashboardResponse:
    """
    Set default view for a dashboard - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        request: Set default view request

    Returns:
        Updated dashboard response
    """
    try:
        updated_dashboard = DashboardCRUD.set_default_view(dashboard_id, request.view_alias)

        return DashboardResponse(**updated_dashboard.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def execute_dashboard(
    dashboard_id: UUID,
    view_alias: Optional[str] = None
) -> DashboardExecutionResponse:
    """
    Execute a dashboard - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        view_alias: Optional specific view to execute

    Returns:
        Dashboard execution response
    """
    try:
        execution_result = DashboardExecutionService.execute_dashboard(dashboard_id, view_alias)

        return DashboardExecutionResponse(**execution_result.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def execute_dashboard_view(
    dashboard_id: UUID,
    view_alias: str
) -> DashboardViewExecutionResponse:
    """
    Execute a specific dashboard view - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        view_alias: View alias

    Returns:
        Dashboard view execution response
    """
    try:
        execution_result = DashboardExecutionService.execute_view(dashboard_id, view_alias)

        return DashboardViewExecutionResponse(**execution_result.model_dump())
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def execute_widget(
    dashboard_id: UUID,
    view_alias: str,
    widget_alias: str
) -> WidgetExecutionResponse:
    """
    Execute a specific widget - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        view_alias: View alias
        widget_alias: Widget alias

    Returns:
        Widget execution response
    """
    try:
        from cortex.core.services.metrics.execution import MetricExecutionService
        from cortex.core.exceptions.dashboards import (
            DashboardDoesNotExistError,
            DashboardViewDoesNotExistError,
            WidgetExecutionError
        )
        from cortex.core.dashboards.transformers import MetricExecutionResult

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
            error_data = _create_error_chart_data(execution_result.get("error", "Metric execution failed"))

            return WidgetExecutionResponse(
                widget_alias=widget_alias,
                data=error_data,
                execution_time_ms=execution_result.get("metadata", {}).get("execution_time_ms", 0.0),
                error=execution_result.get("error")
            )

        # Convert execution result to metric execution result format
        metric_result = _convert_to_metric_execution_result(execution_result)

        # Transform data using field mapping
        transformed_data = _transform_widget_data_with_mapping(target_widget, metric_result)

        return WidgetExecutionResponse(
            widget_alias=widget_alias,
            data=transformed_data,
            execution_time_ms=execution_result.get("metadata", {}).get("execution_time_ms", 0.0),
            error=None
        )
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def delete_widget(
    dashboard_id: UUID,
    view_alias: str,
    widget_alias: str
) -> DashboardResponse:
    """
    Delete a widget from a dashboard view - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        view_alias: View alias
        widget_alias: Widget alias

    Returns:
        Updated dashboard response
    """
    try:
        from cortex.core.exceptions.dashboards import DashboardDoesNotExistError, DashboardViewDoesNotExistError

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
            raise CortexNotFoundError(f"Widget '{widget_alias}' not found in view '{view_alias}'")

        # Update dashboard in database
        updated_dashboard = DashboardCRUD.update_dashboard(dashboard_id, dashboard)

        return DashboardResponse.model_validate(updated_dashboard, from_attributes=True)
    except Exception as e:
        raise CoreExceptionMapper().map(e)


def preview_dashboard(
    dashboard_id: UUID,
    config: DashboardUpdateRequest
) -> DashboardExecutionResponse:
    """
    Preview dashboard execution without saving - direct Core service call.

    Args:
        dashboard_id: Dashboard ID
        config: Dashboard configuration for preview

    Returns:
        Dashboard execution response
    """
    try:
        from cortex.core.services.metrics.execution import MetricExecutionService
        from cortex.core.dashboards.transformers import MetricExecutionResult
        from cortex.core.dashboards.mapping.base import MappingValidationError

        # Validate the configuration structure
        if not config.views or len(config.views) == 0:
            raise ValueError("Dashboard must have at least one view for preview")

        # Use the first view for preview
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
                            id=uuid4(),
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

                    # Convert to metric execution result format
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
    except Exception as e:
        raise CoreExceptionMapper().map(e)


# Helper functions
def _convert_create_request_to_dashboard(request: DashboardCreateRequest) -> Dashboard:
    """Convert dashboard create request to domain model."""

    # Convert views
    views = []
    default_view_id = None

    for i, view_req in enumerate(request.views):
        # Convert sections
        sections = []
        for section_req in view_req.sections:
            # Convert widgets
            widgets = []
            for widget_req in section_req.widgets:
                # Build DataMapping from request
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
                    widget_kwargs["metric"] = SemanticMetric(
                        id=uuid4(),
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
        created_by=uuid4()
    )

    return dashboard


def _create_error_chart_data(error_message: str):
    """Create a StandardChartData object for error cases with all required fields."""
    from cortex.core.dashboards.transformers import ProcessedChartData, ChartMetadata, StandardChartData

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
    """Transform widget data using field mapping."""
    from typing import Any
    from cortex.core.types.dashboards import AxisDataType
    from cortex.core.dashboards.mapping.base import ColumnMapping, MappingValidationError
    from cortex.core.dashboards.mapping.factory import MappingFactory
    from cortex.core.dashboards.transformers import StandardChartData, ProcessedChartData, ChartMetadata

    def _normalize_axis_type(value: Optional[str], default: str) -> str:
        """Normalize axis data types to valid enum values."""
        if not value:
            return default
        v = str(value).strip().lower()
        if v in {"categorical", "category"}:
            return "categorical"
        if v in {"numerical", "numeric", "number"}:
            return "numerical"
        if v in {"temporal", "time", "date", "datetime"}:
            return "temporal"
        return default

    try:
        # Convert metric result to list of dictionaries
        result_data = []
        for row in metric_result.data:
            row_dict = {}
            for i, column in enumerate(metric_result.columns):
                row_dict[column] = row[i] if i < len(row) else None
            result_data.append(row_dict)

        # Convert request data mapping to FieldMapping
        request_mapping = widget.visualization.data_mapping

        def _mapping_type(m: Any, default: str) -> str:
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

        # Build DataMapping
        domain_data_mapping = DataMapping(
            x_axis=_to_field_mapping(getattr(request_mapping, 'x_axis', None), 'categorical', False),
            y_axes=[
                _to_field_mapping(ym, 'numerical', True, True)
                for ym in (getattr(request_mapping, 'y_axes', None) or [])
            ] or None,
            value_field=_to_field_mapping(getattr(request_mapping, 'value_field', None), 'numerical', True),
            category_field=_to_field_mapping(getattr(request_mapping, 'category_field', None), 'categorical', True),
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

        # If there is no data or columns, return safe default
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
            # Create visualization mapping
            visualization_mapping = MappingFactory.create_mapping(
                visualization_type=widget.visualization.type,
                data_mapping=domain_data_mapping,
                visualization_config=widget.visualization.model_dump()
            )

            # For single_value visualization, skip strict XY validation
            if getattr(widget.visualization.type, 'value', widget.visualization.type) == 'single_value':
                try:
                    required_cols = [domain_data_mapping.value_field.field] if domain_data_mapping.value_field else []
                    for col in required_cols:
                        if col not in metric_result.columns:
                            raise MappingValidationError(col, f"Field '{col}' not found in metric result columns: {metric_result.columns}")
                except Exception:
                    pass
            else:
                # Validate mapping for chart types
                for ym in (domain_data_mapping.y_axes or []):
                    if not getattr(ym, 'data_type', None):
                        ym.data_type = AxisDataType.NUMERICAL
                visualization_mapping.validate(metric_result.columns)

            # Transform data
            transformed_data = visualization_mapping.transform_data(result_data)

        # Build metadata
        x_type = None
        y_type = None
        try:
            if domain_data_mapping.x_axis:
                x_type = getattr(domain_data_mapping.x_axis.data_type, 'value', domain_data_mapping.x_axis.data_type)
            if domain_data_mapping.y_axes and len(domain_data_mapping.y_axes) > 0:
                y_type = getattr(domain_data_mapping.y_axes[0].data_type, 'value', domain_data_mapping.y_axes[0].data_type)
        except Exception:
            pass

        x_src = getattr(request_mapping, 'x_axis', None)
        x_type = x_type or _normalize_axis_type((getattr(x_src, 'data_type', None) or getattr(x_src, 'type', None)), 'categorical')
        if not y_type and getattr(request_mapping, 'y_axes', None):
            first_y = request_mapping.y_axes[0]
            y_type = _normalize_axis_type((getattr(first_y, 'data_type', None) or getattr(first_y, 'type', None)), 'numerical')

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
        return _create_error_chart_data(f"Data transformation failed: {str(e)}")
