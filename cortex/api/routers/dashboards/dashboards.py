from uuid import UUID
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from cortex.api.schemas.requests.dashboards import (
    DashboardCreateRequest, DashboardUpdateRequest, SetDefaultViewRequest
)
from cortex.api.schemas.responses.dashboards import (
    DashboardResponse, DashboardListResponse, DashboardExecutionResponse, DashboardViewExecutionResponse,
    WidgetExecutionResponse
)
from cortex.sdk import CortexClient
from cortex.sdk.exceptions import CortexNotFoundError, CortexValidationError, CortexSDKError

DashboardRouter = APIRouter()

# Module-level SDK client in Direct mode for local Core access
_client = CortexClient(mode="direct")


@DashboardRouter.post(
    "/dashboards",
    response_model=DashboardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Dashboards"]
)
async def create_dashboard(dashboard_data: DashboardCreateRequest):
    """Create a new dashboard with views, sections, and widgets."""
    try:
        return _client.dashboards.create(dashboard_data)
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.get(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def get_dashboard(dashboard_id: UUID):
    """Get a dashboard by ID with all views, sections, and widgets."""
    try:
        return _client.dashboards.get(dashboard_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.get(
    "/environments/{environment_id}/dashboards",
    response_model=DashboardListResponse,
    tags=["Dashboards"]
)
async def get_dashboards_by_environment(environment_id: UUID):
    """Get all dashboards for a specific environment."""
    try:
        return _client.dashboards.list(environment_id)
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.put(
    "/dashboards/{dashboard_id}",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def update_dashboard(dashboard_id: UUID, dashboard_data: DashboardUpdateRequest):
    """Update dashboard metadata (name, description, type, tags)."""
    try:
        return _client.dashboards.update(dashboard_id, dashboard_data)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.delete(
    "/dashboards/{dashboard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Dashboards"]
)
async def delete_dashboard(dashboard_id: UUID):
    """Delete a dashboard and all its related data."""
    try:
        _client.dashboards.delete(dashboard_id)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/default-view",
    response_model=DashboardResponse,
    tags=["Dashboards"]
)
async def set_default_view(dashboard_id: UUID, request: SetDefaultViewRequest):
    """Set the default view for a dashboard."""
    try:
        return _client.dashboards.set_default_view(dashboard_id, request)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Dashboard execution endpoints
@DashboardRouter.post(
    "/dashboards/{dashboard_id}/execute",
    response_model=DashboardExecutionResponse,
    tags=["Dashboards"]
)
async def execute_dashboard(dashboard_id: UUID, view_alias: Optional[str] = None):
    """Execute a dashboard (or specific view) and return chart data for all widgets."""
    try:
        return _client.dashboards.execute(dashboard_id, view_alias)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@DashboardRouter.post(
    "/dashboards/{dashboard_id}/views/{view_alias}/execute",
    response_model=DashboardViewExecutionResponse,
    tags=["Dashboards"]
)
async def execute_dashboard_view(dashboard_id: UUID, view_alias: str):
    """Execute a specific dashboard view and return chart data for all widgets."""
    try:
        return _client.dashboards.execute_view(dashboard_id, view_alias)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        return _client.dashboards.execute_widget(dashboard_id, view_alias, widget_alias)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        return _client.dashboards.delete_widget(dashboard_id, view_alias, widget_alias)
    except CortexNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


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
        return _client.dashboards.preview(dashboard_id, config)
    except CortexValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CortexSDKError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))