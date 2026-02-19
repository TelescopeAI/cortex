# Cortex SDK

Python SDK for the Cortex Semantic Layer Platform. Provides programmatic access to all Cortex features including metrics, data sources, dashboards, and more.

## Quick Start

### Direct Mode (Local)

Connect directly to the Cortex Core services without going through the API server:

```python
from cortex.sdk import CortexClient

# Initialize client in Direct mode
client = CortexClient(mode="direct")

# List metrics in an environment
metrics = client.metrics.list(environment_id=env_id)

# Create a new metric
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest
metric = client.metrics.create(MetricCreateRequest(
    environment_id=env_id,
    data_model_id=model_id,
    name="Total Revenue",
    description="Sum of all revenue",
    sql="SELECT SUM(revenue) as total_revenue FROM sales"
))

# Execute a metric
from cortex.sdk.schemas.requests.metrics import MetricExecutionRequest
result = client.metrics.execute(
    metric_id=metric.id,
    request=MetricExecutionRequest(
        environment_id=env_id,
        limit=100
    )
)

# Clean up
client.close()
```

### API Mode (Remote)

Connect to a remote Cortex API server:

```python
from cortex.sdk import CortexClient

# Initialize client in API mode
client = CortexClient(
    mode="api",
    host="http://localhost:9002/api/v1",
    api_key="your-api-key"
)

# Use the same interface as Direct mode
metrics = client.metrics.list(environment_id=env_id)

client.close()
```

### Context Manager

Use context managers for automatic cleanup:

```python
from cortex.sdk import CortexClient

with CortexClient(mode="direct") as client:
    metrics = client.metrics.list(environment_id=env_id)
    # Client automatically closed
```

### Async Support

For async applications, use `AsyncCortexClient`:

```python
import asyncio
from cortex.sdk import AsyncCortexClient

async def main():
    async with AsyncCortexClient(mode="direct") as client:
        metrics = await client.metrics.list(environment_id=env_id)
        print(f"Found {len(metrics)} metrics")

asyncio.run(main())
```

## Architecture

The SDK uses a unified handler architecture that works for both Direct (local) and API (remote) modes:

```
Client → Handler → [Core Service OR HTTP Request]
```

### Connection Modes

**Direct Mode** (default):
- Connects directly to Cortex Core services
- Fastest performance (no HTTP overhead)
- Best for local development and scripts
- Requires access to the Cortex database

**API Mode**:
- Connects to a remote Cortex API server via HTTP
- Works across networks
- Best for distributed applications
- Requires API server running

## Available Handlers

The SDK provides 13 handlers covering all Cortex operations:

### 1. Metrics Handler

```python
# List metrics
metrics = client.metrics.list(environment_id=env_id)

# Get a specific metric
metric = client.metrics.get(metric_id=metric_id)

# Create a metric
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest
metric = client.metrics.create(MetricCreateRequest(...))

# Update a metric
from cortex.sdk.schemas.requests.metrics import MetricUpdateRequest
metric = client.metrics.update(metric_id, MetricUpdateRequest(...))

# Delete a metric
client.metrics.delete(metric_id)

# Execute a metric
from cortex.sdk.schemas.requests.metrics import MetricExecutionRequest
result = client.metrics.execute(metric_id, MetricExecutionRequest(...))

# Compile a metric (get generated SQL)
sql = client.metrics.compile(metric_id)

# Clone a metric
cloned = client.metrics.clone(metric_id, new_name="Cloned Metric")
```

### 2. Metric Variants Handler

```python
# Create a variant
from cortex.sdk.schemas.requests.metric_variants import MetricVariantCreateRequest
variant = client.metric_variants.create(MetricVariantCreateRequest(...))

# List variants for a metric
variants = client.metric_variants.list(source_metric_id=metric_id)

# Execute a variant
result = client.metric_variants.execute(variant_id, execution_request)

# Detach a variant (convert to independent metric)
metric = client.metric_variants.detach_variant(variant_id)
```

### 3. Data Sources Handler

```python
# Create a data source
from cortex.sdk.schemas.requests.data_sources import DataSourceCreateRequest
source = client.data_sources.create(DataSourceCreateRequest(
    environment_id=env_id,
    name="PostgreSQL Production",
    type="postgresql",
    config={
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "pass"
    }
))

# Test connection
result = client.data_sources.test_connection(source_id)

# Refresh schema
schema = client.data_sources.refresh_schema(source_id)

# Delete with cascade
client.data_sources.delete(source_id, cascade=True)
```

### 4. Data Models Handler

```python
# Create a data model
from cortex.sdk.schemas.requests.data_models import DataModelCreateRequest
model = client.data_models.create(DataModelCreateRequest(...))

# Execute a data model query
result = client.data_models.execute(model_id, execution_request)

# List models
models = client.data_models.list(environment_id=env_id)
```

### 5. File Storage Handler

```python
# Upload a file
from cortex.sdk.schemas.requests.file_storage import FileUploadRequest
file = client.file_storage.upload(FileUploadRequest(
    environment_id=env_id,
    file_path="/path/to/data.csv",
    name="Sales Data"
))

# Download a file
content = client.file_storage.download(file_id)
with open("output.csv", "wb") as f:
    f.write(content)

# Get download URL
url = client.file_storage.get_download_url(file_id)

# Delete file
client.file_storage.delete(file_id, cascade=True)
```

### 6. Dashboards Handler

```python
# Create a dashboard
from cortex.sdk.schemas.requests.dashboards import DashboardCreateRequest
dashboard = client.dashboards.create(DashboardCreateRequest(...))

# Preview dashboard (execute all widgets)
preview = client.dashboards.preview_dashboard(dashboard_id)

# Execute a specific widget
widget_data = client.dashboards.execute_widget(
    dashboard_id=dashboard_id,
    widget_id=widget_id,
    execution_request=request
)

# List dashboards
dashboards = client.dashboards.list(environment_id=env_id)
```

### 7. Workspaces Handler

```python
# Create a workspace
from cortex.sdk.schemas.requests.workspaces import WorkspaceCreateRequest
workspace = client.workspaces.create(WorkspaceCreateRequest(
    name="Production",
    description="Production workspace"
))

# List workspaces
workspaces = client.workspaces.list()

# Update workspace
workspace = client.workspaces.update(workspace_id, update_request)
```

### 8. Environments Handler

```python
# Create an environment
from cortex.sdk.schemas.requests.environments import EnvironmentCreateRequest
env = client.environments.create(EnvironmentCreateRequest(
    workspace_id=workspace_id,
    name="Development",
    description="Dev environment"
))

# List environments
environments = client.environments.list(workspace_id=workspace_id)
```

### 9. Consumers Handler

```python
# Create a consumer
from cortex.sdk.schemas.requests.consumers import ConsumerCreateRequest
consumer = client.consumers.create(ConsumerCreateRequest(...))

# Get consumer with groups
consumer = client.consumers.get(consumer_id)
print(consumer.groups)  # List of consumer groups

# List consumers
consumers = client.consumers.list(environment_id=env_id)
```

### 10. Consumer Groups Handler

```python
# Create a consumer group
from cortex.sdk.schemas.requests.consumer_groups import ConsumerGroupCreateRequest
group = client.consumer_groups.create(ConsumerGroupCreateRequest(
    environment_id=env_id,
    name="Premium Users",
    description="Premium tier customers"
))

# Add member to group
from cortex.sdk.schemas.requests.consumer_groups import ConsumerGroupMembershipRequest
client.consumer_groups.add_member(
    group_id=group_id,
    request=ConsumerGroupMembershipRequest(consumer_id=consumer_id)
)

# Check membership
status = client.consumer_groups.check_membership(group_id, consumer_id)
print(status.is_member)

# Get group with members
group_detail = client.consumer_groups.get_with_members(group_id)
for consumer in group_detail.consumers:
    print(consumer.email)
```

### 11. Query History Handler

```python
# Get query history
from cortex.sdk.schemas.requests.query_history import QueryHistoryFilterRequest
logs = client.query_history.get_query_history(QueryHistoryFilterRequest(
    metric_id=metric_id,
    success=True,
    limit=50
))

# Get execution stats
from cortex.sdk.schemas.requests.query_history import QueryHistoryStatsRequest
stats = client.query_history.get_execution_stats(QueryHistoryStatsRequest(
    metric_id=metric_id,
    time_range="24h"
))
print(f"Success rate: {stats.success_rate}%")

# Get slow queries
from cortex.sdk.schemas.requests.query_history import SlowQueriesRequest
slow = client.query_history.get_slow_queries(SlowQueriesRequest(
    limit=10,
    threshold_ms=1000.0
))
```

### 12. Pre-aggregations Handler

```python
# Create/update a pre-aggregation spec
from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest
result = client.preaggregations.upsert_preaggregation_spec(
    PreAggregationUpsertRequest(...)
)

# Build/refresh a pre-aggregation
status = client.preaggregations.refresh_preaggregation_spec(
    spec_id="daily_sales",
    dry_run=False
)

# Get status
status = client.preaggregations.get_preaggregation_status(spec_id)
```

### 13. Admin Handler

```python
# Evict cache entries (admin only)
result = client.admin.evict_cache()
print(f"Evicted {result.evicted_files} files")

# Get cache status
status = client.admin.get_cache_status()
print(f"Cache: {status.cache_size_gb:.2f} GB / {status.max_size_gb} GB")
print(f"Entries: {status.entries_count}")
```

## Context Management

Set workspace and environment context to avoid passing IDs repeatedly:

```python
client = CortexClient(
    mode="direct",
    workspace_id=workspace_id,
    environment_id=env_id
)

# Now operations use the context automatically
metrics = client.metrics.list()  # Uses env_id from client context
```

Temporarily switch context:

```python
# Temporary workspace switch
with client.with_workspace(other_workspace_id):
    # Operations use other_workspace_id
    workspaces = client.workspaces.list()

# Back to original workspace_id

# Temporary environment switch
with client.with_environment(prod_env_id):
    metrics = client.metrics.list()  # Uses prod_env_id
```

## Hooks System

Hooks allow you to intercept and react to SDK operations:

### Built-in Hooks

```python
from cortex.sdk import CortexClient
from cortex.sdk.hooks.builtin import LoggingHook, MetricsHook

client = CortexClient(
    mode="direct",
    hooks=[
        LoggingHook(),  # Logs all operations
        MetricsHook()   # Collects operation metrics
    ]
)
```

### Custom Hooks

```python
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import HookEventType

class CustomHook(BaseHook):
    """Custom hook example."""

    def execute(self, context: EventContext) -> EventContext:
        """Execute hook logic."""
        if context.event_type == HookEventType.BEFORE:
            print(f"Starting: {context.operation}")
        elif context.event_type == HookEventType.AFTER:
            print(f"Completed: {context.operation}")
        elif context.event_type == HookEventType.ERROR:
            print(f"Error in {context.operation}: {context.error}")

        return context

# Use custom hook
client = CortexClient(mode="direct", hooks=[CustomHook()])
```

## Error Handling

The SDK provides typed exceptions for all error cases:

```python
from cortex.sdk import (
    CortexClient,
    CortexNotFoundError,
    CortexValidationError,
    CortexAuthenticationError,
    CortexConnectionError,
    CortexTimeoutError
)

client = CortexClient(mode="api", host="http://localhost:9002/api/v1")

try:
    metric = client.metrics.get(metric_id)
except CortexNotFoundError:
    print("Metric not found")
except CortexValidationError as e:
    print(f"Validation error: {e}")
except CortexAuthenticationError:
    print("Authentication failed")
except CortexConnectionError:
    print("Could not connect to API server")
except CortexTimeoutError:
    print("Request timed out")
```

## Authentication

### API Key Authentication

```python
from cortex.sdk import CortexClient

client = CortexClient(
    mode="api",
    host="http://localhost:9002/api/v1",
    api_key="your-api-key"
)
```

### Custom Authentication

```python
from cortex.sdk import CortexClient, BaseAuthProvider

class CustomAuthProvider(BaseAuthProvider):
    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.get_token()}"}

    def get_token(self) -> str:
        # Custom token retrieval logic
        return "custom-token"

client = CortexClient(
    mode="api",
    host="http://localhost:9002/api/v1",
    auth_provider=CustomAuthProvider()
)
```

## Configuration

### Environment Variables

```bash
# Connection
export CORTEX_MODE=api
export CORTEX_HOST=http://localhost:9002/api/v1
export CORTEX_API_KEY=your-api-key

# Context
export CORTEX_WORKSPACE_ID=550e8400-e29b-41d4-a716-446655440000
export CORTEX_ENVIRONMENT_ID=550e8400-e29b-41d4-a716-446655440001

# HTTP Settings
export CORTEX_TIMEOUT=30
export CORTEX_MAX_RETRIES=3
```

### Settings Object

```python
from cortex.sdk import CortexClient, CortexSDKSettings, ConnectionMode

settings = CortexSDKSettings(
    mode=ConnectionMode.API,
    host="http://localhost:9002/api/v1",
    api_key="your-api-key",
    timeout=30,
    max_retries=3
)

client = CortexClient(settings=settings)
```

## Advanced Usage

### Retry Configuration

The HTTP client automatically retries failed requests with exponential backoff:

```python
client = CortexClient(
    mode="api",
    host="http://localhost:9002/api/v1",
    timeout=30,        # Request timeout (seconds)
    max_retries=3      # Maximum retry attempts
)
```

### File Upload/Download

```python
# Upload file
from cortex.sdk.schemas.requests.file_storage import FileUploadRequest
file = client.file_storage.upload(FileUploadRequest(
    environment_id=env_id,
    file_path="/path/to/large_dataset.csv"
))

# Download file
content = client.file_storage.download(file.id)
with open("downloaded.csv", "wb") as f:
    f.write(content)
```

### Cascade Deletes

Delete resources with their dependencies:

```python
# Delete data source and all dependent metrics
client.data_sources.delete(source_id, cascade=True)

# Delete file and all dependent data sources
client.file_storage.delete(file_id, cascade=True)
```

## Type Safety

The SDK uses Pydantic models for all requests and responses, providing:

- Runtime validation
- IDE autocomplete
- Type hints
- Clear error messages

```python
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest

# IDE autocomplete and type checking
request = MetricCreateRequest(
    environment_id=env_id,
    data_model_id=model_id,
    name="Revenue",
    sql="SELECT SUM(amount) FROM sales"
)

# Validation error if required fields missing or types wrong
metric = client.metrics.create(request)
```

## Performance Tips

1. **Use Direct mode for local development** - Fastest performance
2. **Set context at client level** - Avoid passing IDs repeatedly
3. **Use context managers** - Automatic cleanup
4. **Enable connection pooling** - For API mode with high request volume
5. **Use pre-aggregations** - For frequently executed metrics

## Examples

### Complete Workflow

```python
from cortex.sdk import CortexClient
from cortex.sdk.schemas.requests.workspaces import WorkspaceCreateRequest
from cortex.sdk.schemas.requests.environments import EnvironmentCreateRequest
from cortex.sdk.schemas.requests.data_sources import DataSourceCreateRequest
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest, MetricExecutionRequest

with CortexClient(mode="direct") as client:
    # 1. Create workspace
    workspace = client.workspaces.create(WorkspaceCreateRequest(
        name="My Workspace"
    ))

    # 2. Create environment
    env = client.environments.create(EnvironmentCreateRequest(
        workspace_id=workspace.id,
        name="Production"
    ))

    # 3. Create data source
    source = client.data_sources.create(DataSourceCreateRequest(
        environment_id=env.id,
        name="PostgreSQL",
        type="postgresql",
        config={
            "host": "localhost",
            "database": "mydb"
        }
    ))

    # 4. Create metric
    metric = client.metrics.create(MetricCreateRequest(
        environment_id=env.id,
        data_source_id=source.id,
        name="Total Sales",
        sql="SELECT SUM(amount) as total FROM sales"
    ))

    # 5. Execute metric
    result = client.metrics.execute(
        metric_id=metric.id,
        request=MetricExecutionRequest(environment_id=env.id)
    )

    print(f"Total Sales: {result.data}")
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and guidelines.

## License

See [LICENSE](../LICENSE) for details.

## Support

- Documentation: https://docs.cortex.dev
- GitHub Issues: https://github.com/cortex/cortex/issues
- Slack: https://cortex-community.slack.com
