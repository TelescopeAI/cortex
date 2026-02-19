# Cortex SDK

Python SDK for the Cortex Semantic Layer Platform. Provides programmatic access to all Cortex features including metrics, data sources, dashboards, and more.

## Quick Start

### Direct Mode (Local)

Connect directly to the Cortex Core services without going through the API server:

```python
from cortex.sdk import CortexClient
from uuid import UUID

# Initialize client in Direct mode
client = CortexClient(mode="direct")

# List metrics in an environment
env_id = UUID("your-environment-id")
metrics = client.metrics.list(environment_id=env_id)

# Create a semantic metric using proper schema
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension

metric = client.metrics.create(MetricCreateRequest(
    data_model_id=model_id,
    name="monthly_revenue",
    description="Total revenue aggregated by month",
    table_name="sales",
    measures=[
        SemanticMeasure(
            name="revenue",
            type="sum",
            query="amount",  # Column reference
            formatting=[{
                "name": "currency",
                "type": "format",
                "mode": "post_query",
                "format_string": "${:,.2f}"
            }]
        )
    ],
    dimensions=[
        SemanticDimension(
            name="month",
            query="sale_date",  # Column reference
            type="time"
        )
    ]
))

# Execute the metric
from cortex.sdk.schemas.requests.metrics import MetricExecutionRequest
result = client.metrics.execute(
    metric_id=metric.id,
    request=MetricExecutionRequest(
        limit=100,
        filters={"country": "US"}
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
        print(f"Found {len(metrics.metrics)} metrics")

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
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest, MetricUpdateRequest, MetricExecutionRequest
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension

# List metrics
metrics = client.metrics.list(environment_id=env_id)

# Get a specific metric
metric = client.metrics.get(metric_id=metric_id)

# Create a metric with semantic schema
metric = client.metrics.create(MetricCreateRequest(
    data_model_id=model_id,
    name="daily_sales",
    description="Daily sales aggregated by product",
    table_name="orders",
    measures=[
        SemanticMeasure(
            name="total_sales",
            type="sum",
            query="amount"  # Column reference
        ),
        SemanticMeasure(
            name="order_count",
            type="count",
            query="order_id"
        )
    ],
    dimensions=[
        SemanticDimension(
            name="product",
            query="product_name"
        ),
        SemanticDimension(
            name="date",
            query="order_date",
            type="time"
        )
    ]
))

# Update a metric
updated = client.metrics.update(
    metric_id,
    MetricUpdateRequest(
        environment_id=env_id,
        description="Updated description"
    )
)

# Delete a metric
client.metrics.delete(metric_id)

# Execute a metric
result = client.metrics.execute(
    metric_id,
    MetricExecutionRequest(
        filters={"product": "Widget"},
        limit=100,
        grouped=True
    )
)

# Compile a metric (get generated SQL without executing)
compiled = client.metrics.compile(metric_id)
print(compiled.sql)

# Clone a metric
from cortex.sdk.schemas.requests.metrics import MetricCloneRequest
cloned = client.metrics.clone(
    metric_id,
    MetricCloneRequest(new_name="Cloned Metric")
)
```

### 2. Metric Variants Handler

```python
from cortex.sdk.schemas.requests.metric_variants import MetricVariantCreateRequest

# Create a variant
variant = client.metric_variants.create(MetricVariantCreateRequest(
    source_metric_id=metric_id,
    environment_id=env_id,
    name="Revenue - Q1",
    filters=[{"field": "quarter", "operator": "eq", "value": "Q1"}]
))

# List variants for a metric
variants = client.metric_variants.list(source_metric_id=metric_id)

# Execute a variant
from cortex.sdk.schemas.requests.metric_variants import MetricVariantExecutionRequest
result = client.metric_variants.execute(
    variant_id,
    MetricVariantExecutionRequest(
        environment_id=env_id,
        limit=50
    )
)

# Detach a variant (convert to independent metric)
metric = client.metric_variants.detach_variant(variant_id)
```

### 3. Data Sources Handler

```python
from cortex.sdk.schemas.requests.data_sources import DataSourceCreateRequest

# Create a PostgreSQL data source
source = client.data_sources.create(DataSourceCreateRequest(
    environment_id=env_id,
    name="PostgreSQL Production",
    alias="prod_db",
    source_catalog="default",
    source_type="postgresql",
    config={
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "user",
        "password": "pass"
    }
))

# Test connection
result = client.data_sources.ping(source.id)
print(f"Connection status: {result['status']}")

# Get schema
schema = client.data_sources.get_schema(source.id)
print(f"Tables: {schema['tables']}")

# List data sources
sources = client.data_sources.list(environment_id=env_id)

# Delete with cascade (removes dependent metrics)
client.data_sources.delete(source.id, cascade=True)
```

### 4. Data Models Handler

```python
from cortex.sdk.schemas.requests.data_models import DataModelCreateRequest

# Create a data model
model = client.data_models.create(DataModelCreateRequest(
    environment_id=env_id,
    data_source_id=source_id,
    name="Sales Model",
    tables=["orders", "customers", "products"]
))

# Execute a data model query
from cortex.sdk.schemas.requests.data_models import ModelExecutionRequest
result = client.data_models.execute(
    model.id,
    ModelExecutionRequest(
        metric_alias="revenue",
        parameters={"limit": 100}
    )
)

# List models
models = client.data_models.list(environment_id=env_id)
```

### 5. File Storage Handler

```python
# Upload a file
with open("/path/to/data.csv", "rb") as f:
    content = f.read()

result = client.file_storage.upload(
    environment_id=env_id,
    files=[("data.csv", content)],
    overwrite=False
)
print(f"Uploaded file IDs: {result['file_ids']}")

# List files
files = client.file_storage.list(environment_id=env_id, limit=10)

# Get file info
file_info = client.file_storage.get(file_id)

# Download a file
content = client.file_storage.download(file_id)
with open("output.csv", "wb") as f:
    f.write(content)

# Get download URL
url = client.file_storage.get_download_url(file_id)

# Delete file (with cascade to remove dependent data sources/metrics)
client.file_storage.delete(file_id, environment_id=env_id, cascade=True)
```

### 6. Dashboards Handler

```python
from cortex.sdk.schemas.requests.dashboards import DashboardCreateRequest
from cortex.core.dashboards.types import DashboardType

# Create a dashboard
dashboard = client.dashboards.create(DashboardCreateRequest(
    environment_id=env_id,
    name="Sales Dashboard",
    description="Real-time sales metrics",
    type=DashboardType.OPERATIONAL,
    views=[{
        "alias": "overview",
        "name": "Overview",
        "widgets": [
            {
                "alias": "revenue_chart",
                "type": "bar",
                "metric_id": str(metric_id),
                "position": {"x": 0, "y": 0, "w": 6, "h": 4}
            }
        ]
    }]
))

# Execute dashboard (all widgets)
result = client.dashboards.execute(dashboard.id)
print(f"Execution time: {result.total_execution_time_ms}ms")

# Execute specific view
view_result = client.dashboards.execute_view(dashboard.id, "overview")

# Execute specific widget
widget_result = client.dashboards.execute_widget(
    dashboard.id,
    view_alias="overview",
    widget_alias="revenue_chart"
)

# List dashboards
dashboards = client.dashboards.list(environment_id=env_id)

# Delete dashboard
client.dashboards.delete(dashboard.id)
```

### 7. Workspaces Handler

```python
from cortex.sdk.schemas.requests.workspaces import WorkspaceCreateRequest, WorkspaceUpdateRequest

# Create a workspace
workspace = client.workspaces.create(WorkspaceCreateRequest(
    name="Production Workspace",
    description="Main production workspace"
))

# Get workspace
workspace = client.workspaces.get(workspace_id)

# List all workspaces
workspaces = client.workspaces.list()

# Update workspace
updated = client.workspaces.update(
    workspace_id,
    WorkspaceUpdateRequest(name="Updated Name")
)

# Delete workspace
client.workspaces.delete(workspace_id)
```

### 8. Environments Handler

```python
from cortex.sdk.schemas.requests.environments import EnvironmentCreateRequest, EnvironmentUpdateRequest

# Create an environment
environment = client.environments.create(EnvironmentCreateRequest(
    workspace_id=workspace_id,
    name="Production",
    description="Production environment"
))

# Get environment
env = client.environments.get(environment_id)

# List environments in workspace
environments = client.environments.list(workspace_id=workspace_id)

# Update environment
updated = client.environments.update(
    environment_id,
    EnvironmentUpdateRequest(description="Updated description")
)

# Delete environment
client.environments.delete(environment_id)
```

### 9. Consumers Handler

```python
from cortex.sdk.schemas.requests.consumers import ConsumerCreateRequest

# Create a consumer
consumer = client.consumers.create(ConsumerCreateRequest(
    environment_id=env_id,
    name="Dashboard Service",
    description="Internal dashboard service",
    alias="dashboard_svc"
))

# Get consumer (with groups)
consumer = client.consumers.get(consumer_id)
print(f"Groups: {consumer.groups}")

# List consumers
consumers = client.consumers.list(environment_id=env_id)

# Update consumer
from cortex.sdk.schemas.requests.consumers import ConsumerUpdateRequest
updated = client.consumers.update(
    consumer_id,
    ConsumerUpdateRequest(description="Updated description")
)

# Delete consumer
client.consumers.delete(consumer_id)
```

### 10. Consumer Groups Handler

```python
from cortex.sdk.schemas.requests.consumer_groups import ConsumerGroupCreateRequest

# Create a consumer group
group = client.consumer_groups.create(ConsumerGroupCreateRequest(
    environment_id=env_id,
    name="Analytics Team",
    description="Analytics team members",
    alias="analytics"
))

# Get group
group = client.consumer_groups.get(group_id)

# Get group with members (includes full consumer details)
group_detail = client.consumer_groups.get_with_members(group_id)

# List groups
groups = client.consumer_groups.list(environment_id=env_id)

# Add consumer to group
client.consumer_groups.add_member(group_id, consumer_id)

# Remove consumer from group
client.consumer_groups.remove_member(group_id, consumer_id)

# Check membership
is_member = client.consumer_groups.check_membership(group_id, consumer_id)

# Delete group
client.consumer_groups.delete(group_id)
```

### 11. Query History Handler

```python
from cortex.sdk.schemas.requests.query_history import (
    QueryHistoryFilterRequest,
    QueryHistoryStatsRequest,
    SlowQueriesRequest,
    ClearQueryHistoryRequest
)

# Get query history
logs = client.query_history.get_query_history(
    QueryHistoryFilterRequest(
        metric_id=metric_id,
        success=True,
        limit=50
    )
)

# Get specific query log
log = client.query_history.get_query_log(query_id)

# Get execution statistics
stats = client.query_history.get_execution_stats(
    QueryHistoryStatsRequest(
        metric_id=metric_id,
        time_range="24h"
    )
)
print(f"Success rate: {stats.success_rate}%")

# Get slow queries
slow_queries = client.query_history.get_slow_queries(
    SlowQueriesRequest(
        limit=10,
        threshold_ms=1000.0,
        time_range="7d"
    )
)

# Clear query history (admin only)
from datetime import datetime, timedelta
result = client.query_history.clear_query_history(
    ClearQueryHistoryRequest(
        older_than=datetime.now() - timedelta(days=30)
    )
)
```

### 12. Pre-aggregations Handler

```python
from cortex.sdk.schemas.requests.preaggregations import PreAggregationUpsertRequest

# Create/update a pre-aggregation spec
spec = client.preaggregations.upsert_preaggregation_spec(
    PreAggregationUpsertRequest(
        spec_id="daily_sales",
        metric_id=metric_id,
        dimensions=["date", "product"],
        measures=["revenue", "quantity"],
        refresh_schedule="0 0 * * *"  # Daily at midnight
    )
)

# List specs
specs = client.preaggregations.list_preaggregation_specs()

# Get specific spec
spec = client.preaggregations.get_preaggregation_spec("daily_sales")

# Refresh/build a pre-aggregation
status = client.preaggregations.refresh_preaggregation_spec("daily_sales")

# Get status
status = client.preaggregations.get_preaggregation_status("daily_sales")

# Delete spec
client.preaggregations.delete_preaggregation_spec("daily_sales")
```

### 13. Admin Handler

```python
# Evict LRU cache entries (for distributed deployments)
result = client.admin.evict_cache()
print(f"Evicted {result.evicted_files} files")

# Get cache status
status = client.admin.get_cache_status()
print(f"Cache: {status.cache_size_gb:.2f} GB / {status.max_size_gb} GB")
print(f"Entries: {status.entries_count}")
```

## Error Handling

The SDK provides typed exceptions for consistent error handling:

```python
from cortex.sdk.exceptions import (
    CortexSDKError,
    CortexNotFoundError,
    CortexValidationError,
    CortexAuthenticationError,
    CortexAuthorizationError,
    CortexConnectionError,
    CortexTimeoutError
)

try:
    metric = client.metrics.get(metric_id)
except CortexNotFoundError as e:
    print(f"Metric not found: {e}")
except CortexValidationError as e:
    print(f"Validation error: {e}")
    if e.details:
        print(f"Details: {e.details}")
except CortexConnectionError as e:
    print(f"Connection error: {e}")
except CortexSDKError as e:
    print(f"SDK error: {e}")
```

## Hooks System

The SDK includes a powerful hooks system for custom logic:

```python
from cortex.sdk.hooks.base import BaseHook
from cortex.sdk.hooks.contexts import EventContext
from cortex.sdk.events.types import HookEventType

class LoggingHook(BaseHook):
    """Log all operations"""

    def on_event(self, context: EventContext) -> EventContext:
        if context.event_type == HookEventType.BEFORE:
            print(f"Starting {context.operation}")
        elif context.event_type == HookEventType.AFTER:
            print(f"Completed {context.operation}")
        elif context.event_type == HookEventType.ERROR:
            print(f"Error in {context.operation}: {context.error}")
        return context

# Use hooks with client
client = CortexClient(
    mode="direct",
    hooks=[LoggingHook()]
)

# Hooks fire for create, update, delete operations
metric = client.metrics.create(request)  # LoggingHook fires
```

### Built-in Hooks

```python
from cortex.sdk.hooks.builtin import MetricsTrackingHook, ValidationHook

# Track metric operations
tracking_hook = MetricsTrackingHook()

# Add validation before operations
validation_hook = ValidationHook()

client = CortexClient(
    mode="direct",
    hooks=[tracking_hook, validation_hook]
)
```

## Context Management

Set default workspace/environment context:

```python
# Set context for all operations
client = CortexClient(
    mode="direct",
    workspace_id=workspace_id,
    environment_id=env_id
)

# Operations use context automatically
metrics = client.metrics.list()  # Uses env_id from client

# Temporarily switch context
with client.with_environment(other_env_id):
    metrics = client.metrics.list()  # Uses other_env_id
# Back to original env_id

# Change context permanently
client.set_environment(new_env_id)
```

## Configuration

Configure SDK behavior via environment variables or settings:

```python
from cortex.sdk.config import CortexSDKSettings

# Via environment variables
# CORTEX_SDK_MODE=direct
# CORTEX_SDK_HOST=http://localhost:9002/api/v1
# CORTEX_SDK_API_KEY=your-key
# CORTEX_SDK_TIMEOUT=30
# CORTEX_SDK_MAX_RETRIES=3

# Or via settings object
settings = CortexSDKSettings(
    mode="api",
    host="http://localhost:9002/api/v1",
    api_key="your-key",
    timeout=30,
    max_retries=3
)

client = CortexClient(settings=settings)
```

## Best Practices

### 1. Use Semantic Schema (Not Raw SQL)

**Good** - Let Cortex generate SQL:
```python
metric = client.metrics.create(MetricCreateRequest(
    data_model_id=model_id,
    name="revenue",
    table_name="sales",
    measures=[
        SemanticMeasure(
            name="total",
            type="sum",
            query="amount"  # Column reference
        )
    ]
))
```

**Bad** - Don't write raw SQL:
```python
# ❌ This won't work - there's no 'sql' field
metric = client.metrics.create(MetricCreateRequest(
    sql="SELECT SUM(amount) FROM sales"  # Wrong!
))
```

### 2. Use Context Managers

```python
# Always use context managers for automatic cleanup
with CortexClient(mode="direct") as client:
    metrics = client.metrics.list(environment_id=env_id)
    # Client auto-closed
```

### 3. Handle Exceptions Properly

```python
try:
    metric = client.metrics.create(request)
except CortexValidationError as e:
    # Handle validation errors
    print(f"Validation failed: {e.details}")
except CortexNotFoundError:
    # Handle not found
    pass
```

### 4. Use Cascade Delete Carefully

```python
# Cascade delete removes all dependencies
client.data_sources.delete(source_id, cascade=True)  # Deletes metrics too!

# Without cascade, fails if dependencies exist
client.data_sources.delete(source_id, cascade=False)  # Raises error if metrics exist
```

### 5. Leverage Hooks for Cross-Cutting Concerns

```python
# Use hooks for logging, metrics, validation
client = CortexClient(
    mode="direct",
    hooks=[LoggingHook(), MetricsHook(), ValidationHook()]
)
```

## Complete Example

```python
from cortex.sdk import CortexClient
from cortex.sdk.schemas.requests.workspaces import WorkspaceCreateRequest
from cortex.sdk.schemas.requests.environments import EnvironmentCreateRequest
from cortex.sdk.schemas.requests.data_sources import DataSourceCreateRequest
from cortex.sdk.schemas.requests.data_models import DataModelCreateRequest
from cortex.sdk.schemas.requests.metrics import MetricCreateRequest
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension

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
        source_type="postgresql",
        alias="prod_db",
        source_catalog="default",
        config={
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "username": "user",
            "password": "pass"
        }
    ))

    # 4. Create data model
    model = client.data_models.create(DataModelCreateRequest(
        environment_id=env.id,
        data_source_id=source.id,
        name="Sales Model",
        tables=["orders", "customers"]
    ))

    # 5. Create semantic metric
    metric = client.metrics.create(MetricCreateRequest(
        data_model_id=model.id,
        name="monthly_revenue",
        table_name="orders",
        measures=[
            SemanticMeasure(
                name="revenue",
                type="sum",
                query="amount",
                formatting=[{
                    "name": "currency",
                    "type": "format",
                    "mode": "post_query",
                    "format_string": "${:,.2f}"
                }]
            )
        ],
        dimensions=[
            SemanticDimension(
                name="month",
                query="order_date",
                type="time"
            )
        ]
    ))

    # 6. Execute metric
    from cortex.sdk.schemas.requests.metrics import MetricExecutionRequest
    result = client.metrics.execute(
        metric.id,
        MetricExecutionRequest(limit=12)
    )

    print(f"Revenue data: {result.data}")
```

## License

See the main Cortex project for license information.
