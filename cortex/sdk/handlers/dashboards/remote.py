"""
Dashboards remote handler - HTTP API calls.

Handles dashboard operations in API mode.
"""
from typing import Optional
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
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


def create_dashboard(
    client: CortexHTTPClient,
    request: DashboardCreateRequest
) -> DashboardResponse:
    """
    Create a new dashboard - HTTP API call.

    Args:
        client: HTTP client
        request: Dashboard creation request

    Returns:
        Created dashboard response
    """
    response = client.post("/dashboards", data=request.model_dump())
    return DashboardResponse(**response)


def get_dashboard(
    client: CortexHTTPClient,
    dashboard_id: UUID
) -> DashboardResponse:
    """
    Get a dashboard by ID - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID

    Returns:
        Dashboard response
    """
    response = client.get(f"/dashboards/{dashboard_id}")
    return DashboardResponse(**response)


def list_dashboards(
    client: CortexHTTPClient,
    environment_id: UUID
) -> DashboardListResponse:
    """
    List dashboards by environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID

    Returns:
        List of dashboard responses
    """
    response = client.get(f"/environments/{environment_id}/dashboards")
    return DashboardListResponse(**response)


def update_dashboard(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    request: DashboardUpdateRequest
) -> DashboardResponse:
    """
    Update a dashboard - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        request: Update request

    Returns:
        Updated dashboard response
    """
    response = client.put(f"/dashboards/{dashboard_id}", data=request.model_dump())
    return DashboardResponse(**response)


def delete_dashboard(
    client: CortexHTTPClient,
    dashboard_id: UUID
) -> None:
    """
    Delete a dashboard - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
    """
    client.delete(f"/dashboards/{dashboard_id}")


def set_default_view(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    request: SetDefaultViewRequest
) -> DashboardResponse:
    """
    Set default view for a dashboard - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        request: Set default view request

    Returns:
        Updated dashboard response
    """
    response = client.post(f"/dashboards/{dashboard_id}/default-view", data=request.model_dump())
    return DashboardResponse(**response)


def execute_dashboard(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    view_alias: Optional[str] = None
) -> DashboardExecutionResponse:
    """
    Execute a dashboard - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        view_alias: Optional specific view to execute

    Returns:
        Dashboard execution response
    """
    params = {}
    if view_alias:
        params["view_alias"] = view_alias

    response = client.post(f"/dashboards/{dashboard_id}/execute", params=params)
    return DashboardExecutionResponse(**response)


def execute_dashboard_view(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    view_alias: str
) -> DashboardViewExecutionResponse:
    """
    Execute a specific dashboard view - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        view_alias: View alias

    Returns:
        Dashboard view execution response
    """
    response = client.post(f"/dashboards/{dashboard_id}/views/{view_alias}/execute")
    return DashboardViewExecutionResponse(**response)


def execute_widget(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    view_alias: str,
    widget_alias: str
) -> WidgetExecutionResponse:
    """
    Execute a specific widget - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        view_alias: View alias
        widget_alias: Widget alias

    Returns:
        Widget execution response
    """
    response = client.post(f"/dashboards/{dashboard_id}/views/{view_alias}/widgets/{widget_alias}/execute")
    return WidgetExecutionResponse(**response)


def delete_widget(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    view_alias: str,
    widget_alias: str
) -> DashboardResponse:
    """
    Delete a widget from a dashboard view - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        view_alias: View alias
        widget_alias: Widget alias

    Returns:
        Updated dashboard response
    """
    response = client.delete(f"/dashboards/{dashboard_id}/views/{view_alias}/widgets/{widget_alias}")
    return DashboardResponse(**response)


def preview_dashboard(
    client: CortexHTTPClient,
    dashboard_id: UUID,
    config: DashboardUpdateRequest
) -> DashboardExecutionResponse:
    """
    Preview dashboard execution without saving - HTTP API call.

    Args:
        client: HTTP client
        dashboard_id: Dashboard ID
        config: Dashboard configuration for preview

    Returns:
        Dashboard execution response
    """
    response = client.post(f"/dashboards/{dashboard_id}/preview", data=config.model_dump())
    return DashboardExecutionResponse(**response)
