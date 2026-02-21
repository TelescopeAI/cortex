"""
Data sources remote handler - HTTP API calls.

Handles data source operations in API mode.
"""
from typing import List, Dict, Any
from uuid import UUID

from cortex.sdk.clients.http_client import CortexHTTPClient
from cortex.sdk.schemas.requests.data_sources import (
    DataSourceCreateRequest,
    DataSourceUpdateRequest,
    DataSourceRebuildRequest,
    DataSourceQueryRequest,
)
from cortex.sdk.schemas.responses.data_sources import (
    DataSourceResponse,
    DataSourceRebuildResponse,
    DataSourceQueryResponse,
)


def create_data_source(
    client: CortexHTTPClient,
    request: DataSourceCreateRequest
) -> DataSourceResponse:
    """
    Create a new data source - HTTP API call.

    Args:
        client: HTTP client
        request: Data source creation request

    Returns:
        Created data source response
    """
    response = client.post("/data/sources", data=request.model_dump())
    return DataSourceResponse(**response)


def get_data_source(client: CortexHTTPClient, data_source_id: UUID) -> DataSourceResponse:
    """
    Get a data source by ID - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Data source response
    """
    response = client.get(f"/data/sources/{data_source_id}")
    return DataSourceResponse(**response)


def list_data_sources(
    client: CortexHTTPClient,
    environment_id: UUID
) -> List[DataSourceResponse]:
    """
    List all data sources in an environment - HTTP API call.

    Args:
        client: HTTP client
        environment_id: Environment ID

    Returns:
        List of data source responses
    """
    response = client.get(f"/environments/{environment_id}/data/sources")
    return [DataSourceResponse(**ds) for ds in response]


def update_data_source(
    client: CortexHTTPClient,
    data_source_id: UUID,
    request: DataSourceUpdateRequest
) -> DataSourceResponse:
    """
    Update a data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID
        request: Update request

    Returns:
        Updated data source response
    """
    response = client.put(f"/data/sources/{data_source_id}", data=request.model_dump())
    return DataSourceResponse(**response)


def delete_data_source(
    client: CortexHTTPClient,
    data_source_id: UUID,
    cascade: bool = False
) -> None:
    """
    Delete a data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID
        cascade: If true, delete all dependent metrics
    """
    params = {"cascade": cascade}
    client.delete(f"/data/sources/{data_source_id}", params=params)


def ping_data_source(client: CortexHTTPClient, data_source_id: UUID) -> Dict[str, Any]:
    """
    Test connectivity to a data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Ping result dictionary
    """
    response = client.post(f"/data/sources/{data_source_id}/ping")
    return response


def get_data_source_schema(client: CortexHTTPClient, data_source_id: UUID) -> Dict[str, Any]:
    """
    Get the schema information for a data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Schema information dictionary
    """
    response = client.get(f"/data/sources/{data_source_id}/schema")
    return response


def get_data_source_schema_humanized(
    client: CortexHTTPClient,
    data_source_id: UUID
) -> Dict[str, Any]:
    """
    Get a human-readable description of the data source schema - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Humanized schema information dictionary
    """
    response = client.get(f"/data/sources/{data_source_id}/schema/humanized")
    return response


def query_data_source(
    client: CortexHTTPClient,
    data_source_id: UUID,
    request: DataSourceQueryRequest,
) -> DataSourceQueryResponse:
    """
    Run a direct query against a data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID
        request: Query request

    Returns:
        Query response with results
    """
    response = client.post(
        f"/data/sources/{data_source_id}/query",
        data=request.model_dump(),
    )
    return DataSourceQueryResponse(**response)


def rebuild_data_source(
    client: CortexHTTPClient,
    data_source_id: UUID,
    request: DataSourceRebuildRequest
) -> DataSourceRebuildResponse:
    """
    Rebuild a spreadsheet data source from its original file - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID
        request: Rebuild request

    Returns:
        Rebuild response
    """
    response = client.post(
        f"/data/sources/{data_source_id}/rebuild",
        data=request.model_dump()
    )
    return DataSourceRebuildResponse(**response)


def refresh_spreadsheet_source(
    client: CortexHTTPClient,
    data_source_id: UUID
) -> Dict[str, Any]:
    """
    Refresh a spreadsheet data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Refresh result dictionary
    """
    response = client.post(f"/data/sources/{data_source_id}/refresh")
    return response


def get_spreadsheet_status(
    client: CortexHTTPClient,
    data_source_id: UUID
) -> Dict[str, Any]:
    """
    Get sync status and table list for a spreadsheet data source - HTTP API call.

    Args:
        client: HTTP client
        data_source_id: Data source ID

    Returns:
        Status information dictionary
    """
    response = client.get(f"/data/sources/{data_source_id}/status")
    return response
