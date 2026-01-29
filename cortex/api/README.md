# Cortex API Reference

The Cortex API provides RESTful endpoints for all platform operations, from workspace management to metric execution. All functionality is exposed via a FastAPI-powered REST API with auto-generated OpenAPI documentation.

![API Documentation](../docs/assets/api_documentation_screenshot.png)
*Interactive API documentation interface*

## Overview

The Cortex API follows REST principles and provides:

- **Auto-generated Documentation**: OpenAPI/Swagger specs with Scalar FastAPI
- **Request/Response Validation**: Comprehensive Pydantic models
- **Type Safety**: Full TypeScript definitions (generated)
- **Authentication**: Token-based auth (when implemented)
- **Error Handling**: Standardized error responses
- **Versioning**: API versioning support (`/api/v1/`)

## Accessing API Documentation

Start the Cortex API server and access the documentation:

```bash
# Start API server
python -m cortex.api

# Access interactive documentation
# Scalar UI (recommended): http://localhost:9002/docs
# Classic Swagger UI: http://localhost:9002/docs/classic
# ReDoc UI: http://localhost:9002/redoc
```

## Base URL

```
http://localhost:9002/api/v1
```

For production, replace with your deployed URL.

## Core API Endpoints

### Workspaces

Top-level organizational units for multi-tenancy.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workspaces` | List all workspaces |
| `POST` | `/workspaces` | Create a workspace |
| `GET` | `/workspaces/{id}` | Get workspace details |
| `PUT` | `/workspaces/{id}` | Update workspace |
| `DELETE` | `/workspaces/{id}` | Delete workspace |

### Environments

Development stages within workspaces (dev, staging, production).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/environments` | List environments |
| `POST` | `/environments` | Create environment |
| `GET` | `/environments/{id}` | Get environment details |
| `PUT` | `/environments/{id}` | Update environment |
| `DELETE` | `/environments/{id}` | Delete environment |

### Data Sources

Database connection management and file storage.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/environments/{environment_id}/data/sources` | List data sources by environment |
| `POST` | `/data/sources` | Create data source |
| `GET` | `/data/sources/{id}` | Get data source details |
| `PUT` | `/data/sources/{id}` | Update data source |
| `DELETE` | `/data/sources/{id}?cascade=false` | Delete data source (with optional cascade) |
| `POST` | `/data/sources/{id}/test` | Test connection |
| `POST` | `/data/sources/{id}/ping` | Ping connection |
| `GET` | `/data/sources/{id}/schema` | Get data source schema |
| `GET` | `/data/sources/{id}/tables` | List tables |
| `GET` | `/data/sources/{id}/tables/{name}/columns` | List columns |
| `POST` | `/data/sources/{id}/rebuild` | Rebuild data source |

**Spreadsheet & File Management:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/data/sources/upload` | Upload files (CSV, spreadsheets) |
| `GET` | `/data/sources/files` | List uploaded files |
| `DELETE` | `/data/sources/files/{file_id}?cascade=false` | Delete file (with optional cascade) |
| `POST` | `/data/sources/discover` | Discover sheets in uploaded files |
| `POST` | `/data/sources/preview` | Preview sheet data |
| `POST` | `/data/sources/{id}/refresh` | Refresh spreadsheet data source |

### Data Models

Business data model definitions.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/data/models` | List data models |
| `POST` | `/data/models` | Create data model |
| `GET` | `/data/models/{id}` | Get data model details |
| `PUT` | `/data/models/{id}` | Update data model |
| `DELETE` | `/data/models/{id}` | Delete data model |

### Metrics

Semantic metric creation and execution.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/metrics` | List metrics |
| `POST` | `/metrics` | Create metric |
| `GET` | `/metrics/{id}` | Get metric details |
| `PUT` | `/metrics/{id}` | Update metric |
| `DELETE` | `/metrics/{id}` | Delete metric |
| `POST` | `/metrics/{id}/execute` | Execute metric |
| `POST` | `/metrics/{id}/preview` | Preview metric |
| `GET` | `/metrics/{id}/history` | Get execution history |

### Dashboards

Dashboard and widget management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboards` | List dashboards |
| `POST` | `/dashboards` | Create dashboard |
| `GET` | `/dashboards/{id}` | Get dashboard details |
| `PUT` | `/dashboards/{id}` | Update dashboard |
| `DELETE` | `/dashboards/{id}` | Delete dashboard |
| `POST` | `/dashboards/{id}/execute` | Execute all widgets |
| `GET` | `/dashboards/{id}/widgets` | List widgets |
| `POST` | `/dashboards/{id}/widgets` | Add widget |
| `PUT` | `/dashboards/{id}/widgets/{widget_id}` | Update widget |
| `DELETE` | `/dashboards/{id}/widgets/{widget_id}` | Delete widget |

### Consumers

End user management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/consumers` | List consumers |
| `POST` | `/consumers` | Create consumer |
| `GET` | `/consumers/{id}` | Get consumer details |
| `PUT` | `/consumers/{id}` | Update consumer |
| `DELETE` | `/consumers/{id}` | Delete consumer |

### Consumer Groups

User group management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/consumers/groups` | List groups |
| `POST` | `/consumers/groups` | Create group |
| `GET` | `/consumers/groups/{id}` | Get group details |
| `PUT` | `/consumers/groups/{id}` | Update group |
| `DELETE` | `/consumers/groups/{id}` | Delete group |
| `POST` | `/consumers/groups/{id}/members` | Add member |
| `DELETE` | `/consumers/groups/{id}/members/{consumer_id}` | Remove member |

### Query History

Query execution logs and analytics.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/query/history` | List query history |
| `GET` | `/query/history/{id}` | Get query details |
| `GET` | `/query/history/stats` | Get statistics |
| `GET` | `/query/history/slow` | Get slow queries |

### Pre-aggregations

Rollup table management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/pre-aggregations` | List pre-aggregations |
| `POST` | `/pre-aggregations` | Create pre-aggregation |
| `GET` | `/pre-aggregations/{id}` | Get details |
| `PUT` | `/pre-aggregations/{id}` | Update pre-aggregation |
| `DELETE` | `/pre-aggregations/{id}` | Delete pre-aggregation |
| `POST` | `/pre-aggregations/{id}/refresh` | Trigger refresh |


## Example API Usage

### Python with `httpx`

```python
import httpx

BASE_URL = "http://localhost:9002/api/v1"

# Create a workspace
response = httpx.post(f"{BASE_URL}/workspaces", json={
    "name": "Production Workspace",
    "description": "Main production environment"
})
workspace = response.json()
print(f"Created workspace: {workspace['id']}")

# Create an environment
response = httpx.post(f"{BASE_URL}/environments", json={
    "workspace_id": workspace["id"],
    "name": "Production",
    "description": "Production environment"
})
environment = response.json()

# Create a data source
response = httpx.post(f"{BASE_URL}/data/sources", json={
    "environment_id": environment["id"],
    "name": "Analytics Database",
    "alias": "analytics_db",
    "source_catalog": "database",
    "source_type": "postgresql",
    "config": {
        "host": "localhost",
        "port": 5432,
        "database": "analytics",
        "username": "readonly",
        "password": "secret"
    }
})
data_source = response.json()

# Execute a metric
response = httpx.post(f"{BASE_URL}/metrics/{metric_id}/execute", json={
    "parameters": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    },
    "cache": {
        "enabled": True,
        "ttl": 3600
    }
})
result = response.json()
print(f"Metric result: {result['data']}")
```

### JavaScript with `fetch`

```javascript
const BASE_URL = 'http://localhost:9002/api/v1';

// Create a workspace
const workspace = await fetch(`${BASE_URL}/workspaces`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Production Workspace',
    description: 'Main production environment'
  })
}).then(res => res.json());

// Execute a metric
const result = await fetch(`${BASE_URL}/metrics/${metricId}/execute`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    parameters: {
      start_date: '2024-01-01',
      end_date: '2024-12-31'
    },
    cache: {
      enabled: true,
      ttl: 3600
    }
  })
}).then(res => res.json());

console.log('Metric result:', result.data);
```

### cURL

```bash
# Create a workspace
curl -X POST http://localhost:9002/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Workspace",
    "description": "Main production environment"
  }'

# Execute a metric
curl -X POST http://localhost:9002/api/v1/metrics/{metric_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "cache": {
      "enabled": true,
      "ttl": 3600
    }
  }'
```

## Request/Response Validation

All requests and responses are validated using Pydantic models.

### Request Validation

```python
# Invalid request will return 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Response Schema

```python
# Successful response
{
  "id": "uuid-123",
  "name": "My Workspace",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Metric with ID 'abc-123' not found",
    "details": {
      "metric_id": "abc-123"
    }
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No Content |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `422` | Unprocessable Entity |
| `500` | Internal Server Error |

## Authentication

> [!NOTE]
> Authentication is planned but not yet implemented. All endpoints are currently publicly accessible.

**Planned authentication flow:**

```python
# Login to get token
response = httpx.post(f"{BASE_URL}/auth/login", json={
    "username": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# Use token in requests
headers = {"Authorization": f"Bearer {token}"}
response = httpx.get(f"{BASE_URL}/workspaces", headers=headers)
```

## Rate Limiting

> [!NOTE]
> Rate limiting is planned for future releases.

**Planned rate limits:**
- 100 requests per minute per IP
- 1000 requests per hour per user
- Custom limits for enterprise users

## Pagination

List endpoints support pagination:

```python
# Request with pagination
response = httpx.get(f"{BASE_URL}/metrics", params={
    "limit": 50,
    "offset": 0,
    "sort_by": "created_at",
    "sort_order": "desc"
})

# Response includes pagination metadata
{
  "data": [...],
  "pagination": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

## Filtering & Search

Many list endpoints support filtering:

```python
# Filter metrics by environment
response = httpx.get(f"{BASE_URL}/metrics", params={
    "environment_id": "env-123",
    "search": "revenue"
})
```

## Cascade Delete

Data sources and files support cascade delete to remove dependent entities:

### Delete Data Source with Dependencies

```python
# Attempt to delete a data source
response = httpx.delete(f"{BASE_URL}/data/sources/{source_id}")

# If 409 Conflict returned, dependencies exist
if response.status_code == 409:
    dependencies = response.json()["detail"]
    print(f"Cannot delete: {len(dependencies['dependencies']['metrics'])} dependent metrics")

    # Cascade delete (removes data source + all dependent metrics)
    response = httpx.delete(f"{BASE_URL}/data/sources/{source_id}?cascade=true")
```

### Delete File with Dependencies

```python
# Attempt to delete a file
response = httpx.delete(
    f"{BASE_URL}/data/sources/files/{file_id}",
    params={"environment_id": environment_id}
)

# If 409 Conflict, check which data sources depend on it
if response.status_code == 409:
    dependencies = response.json()["detail"]
    data_sources = dependencies["dependencies"]["data_sources"]
    print(f"File used by {len(data_sources)} data sources")

    # Cascade delete (removes file + all dependent data sources + metrics)
    response = httpx.delete(
        f"{BASE_URL}/data/sources/files/{file_id}?cascade=true",
        params={"environment_id": environment_id}
    )
```

**Response on 409 Conflict:**

```json
{
  "detail": {
    "error": "DataSourceHasDependencies",
    "message": "Cannot delete data source: 3 metrics depend on it",
    "data_source_id": "ds-uuid",
    "dependencies": {
      "metrics": [
        {
          "id": "metric-uuid",
          "name": "Monthly Revenue",
          "alias": "monthly_revenue",
          "version_count": 2
        }
      ]
    }
  }
}
```

## Webhooks

> [!NOTE]
> Webhooks are planned for future releases.

**Planned webhook events:**
- `metric.created`
- `metric.updated`
- `metric.executed`
- `dashboard.created`
- `data_source.connection_failed`

## SDK & Client Libraries

### Python SDK

```bash
pip install telescope-cortex[api]
```

```python
from cortex.api.client import CortexClient

client = CortexClient(base_url="http://localhost:9002")

# Use high-level methods
workspace = client.workspaces.create(name="My Workspace")
metric = client.metrics.get(id="metric-123")
result = client.metrics.execute(id="metric-123", parameters={...})
```

### TypeScript SDK (Planned)

```bash
npm install @telescope/cortex-client
```

```typescript
import { CortexClient } from '@telescope/cortex-client';

const client = new CortexClient({
  baseUrl: 'http://localhost:9002'
});

const workspace = await client.workspaces.create({
  name: 'My Workspace'
});
```

## Best Practices

1. **Use Pagination**: Always use pagination for list endpoints
2. **Handle Errors**: Implement proper error handling
3. **Cache Responses**: Cache frequently accessed data
4. **Validate Input**: Validate data before sending requests
5. **Use SDKs**: Use official SDKs when available
6. **Monitor Rate Limits**: Track API usage to avoid limits
7. **Use HTTPS**: Always use HTTPS in production

## Related Documentation

- [Getting Started](../docs/content/getting-started.md) - API setup and configuration
- [Semantic Layer](../core/semantics/README.md) - Metric definitions
- [Query Engine](../core/query/README.md) - Query execution
- [Dashboards](../core/dashboards/README.md) - Dashboard management
- [Multi Tenancy](../docs/content/multi-tenancy.md) - Workspace and environment isolation
