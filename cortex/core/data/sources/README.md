# Data Sources

The Cortex Data Sources module provides connectors for various database systems and file formats, enabling you to query data from multiple sources through a unified interface.

![Data Source Architecture](../../../docs/assets/data_source_architecture.png)
*Data source connection architecture and flow*

## Overview

Cortex supports multiple data source types:

- **Relational Databases**: PostgreSQL, MySQL, SQLite
- **Cloud Data Warehouses**: Google BigQuery (with more planned)
- **File-Based Sources**: CSV files, Google Sheets
- **In-Memory Analytics**: SQLite for temporary analytics

All data sources are managed through a unified connector interface with consistent configuration and schema introspection capabilities.

## Supported Data Sources

### PostgreSQL

Production-grade relational database with advanced features.

**Configuration:**

```json
{
  "name": "Production Database",
  "alias": "prod_db",
  "source_catalog": "database",
  "source_type": "postgresql",
  "config": {
    "host": "localhost",
    "port": 5432,
    "database": "analytics",
    "username": "user",
    "password": "password",
    "ssl_mode": "require"
  }
}
```

**Features:**
- Advanced SQL support
- Window functions
- CTEs and subqueries
- JSON/JSONB support
- Full-text search

### MySQL

Popular open-source relational database.

**Configuration:**

```json
{
  "name": "MySQL Database",
  "alias": "mysql_db",
  "source_catalog": "database",
  "source_type": "mysql",
  "config": {
    "host": "localhost",
    "port": 3306,
    "database": "analytics",
    "username": "user",
    "password": "password"
  }
}
```

**Features:**
- Optimized GROUP BY
- Fast aggregations
- InnoDB transactions
- Partitioning support

### BigQuery

Google's cloud data warehouse for large-scale analytics.

**Configuration:**

```json
{
  "name": "BigQuery Warehouse",
  "alias": "bq_warehouse",
  "source_catalog": "database",
  "source_type": "bigquery",
  "config": {
    "project_id": "my-project",
    "dataset_id": "analytics",
    "credentials_path": "/path/to/service-account.json"
  }
}
```

**Features:**
- Petabyte-scale queries
- Columnar storage
- Automatic partitioning
- Machine learning integration

### SQLite

Lightweight, file-based database for local analytics.

**Configuration:**

```json
{
  "name": "Local SQLite",
  "alias": "local_db",
  "source_catalog": "database",
  "source_type": "sqlite",
  "config": {
    "database_path": "/path/to/database.db",
    "in_memory": false
  }
}
```

**In-memory mode:**

```json
{
  "config": {
    "in_memory": true
  }
}
```

**Features:**
- Zero configuration
- Portable database files
- In-memory analytics
- Ideal for development

### Spreadsheet Data Sources

Cortex supports CSV files and Google Sheets as data sources with automatic SQLite conversion.

**For detailed spreadsheet configuration, see:**
📖 [Spreadsheet Data Sources Guide](../../connectors/api/sheets/README.md)

**Quick example:**

```json
{
  "name": "Sales Spreadsheet",
  "alias": "sales_sheet",
  "source_catalog": "spreadsheet",
  "source_type": "csv",
  "config": {
    "file_path": "/path/to/sales.csv",
    "has_header": true
  }
}
```

![Schema Introspection](../../../docs/assets/schema_introspection_example.png)
*Schema introspection example showing automatic column detection*

## Connection Management

### Cascade Delete

Cortex provides intelligent dependency tracking for data sources and files. When you attempt to delete a data source or file that has dependent metrics, Cortex returns the dependency tree and allows cascade deletion.

**Delete Data Source:**

```python
import httpx

# Attempt to delete data source
response = httpx.delete(
    f"http://localhost:9002/api/v1/data/sources/{source_id}"
)

# If 409 Conflict, dependencies exist
if response.status_code == 409:
    error = response.json()["detail"]
    print(f"Error: {error['message']}")
    print(f"Dependent metrics: {len(error['dependencies']['metrics'])}")

    # Cascade delete (removes data source + all metrics + versions)
    response = httpx.delete(
        f"http://localhost:9002/api/v1/data/sources/{source_id}?cascade=true"
    )
```

**Delete File:**

```python
# Attempt to delete file
response = httpx.delete(
    f"http://localhost:9002/api/v1/data/sources/files/{file_id}",
    params={"environment_id": env_id}
)

# If 409 Conflict, check dependencies
if response.status_code == 409:
    error = response.json()["detail"]
    data_sources = error["dependencies"]["data_sources"]

    # Cascade delete (removes file + data sources + metrics)
    response = httpx.delete(
        f"http://localhost:9002/api/v1/data/sources/files/{file_id}?cascade=true",
        params={"environment_id": env_id}
    )
```

**Dependency Response Format (409 Conflict):**

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
          "name": "Total Revenue",
          "alias": "total_revenue",
          "version_count": 2
        }
      ]
    }
  }
}
```

### Creating Data Sources

**Via API:**

```python
import httpx

response = httpx.post("http://localhost:9002/api/v1/data/sources", json={
    "environment_id": "env-123",
    "name": "Analytics DB",
    "alias": "analytics",
    "source_catalog": "database",
    "source_type": "postgresql",
    "config": {
        "host": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "readonly",
        "password": "secret"
    }
})

data_source = response.json()
```

**Via Python SDK:**

```python
from cortex.core.data.sources.service import DataSourceService

service = DataSourceService()

data_source = service.create_data_source(
    environment_id="env-123",
    name="Analytics DB",
    alias="analytics",
    source_catalog="database",
    source_type="postgresql",
    config={
        "host": "db.example.com",
        "port": 5432,
        "database": "analytics",
        "username": "readonly",
        "password": "secret"
    }
)
```

### Testing Connections

Test a data source connection before saving:

```python
from cortex.core.connectors.factory import ConnectorFactory

factory = ConnectorFactory()
connector = factory.create_connector(
    source_type="postgresql",
    config=config
)

# Test connection
is_connected = connector.test_connection()
if is_connected:
    print("Connection successful!")
else:
    print("Connection failed")
```

### Connection Pooling

Cortex manages connection pools automatically for optimal performance:

- **Pool Size**: Configurable per data source
- **Connection Reuse**: Persistent connections across requests
- **Automatic Cleanup**: Idle connections are closed after timeout
- **Health Checks**: Periodic connection validation

## Schema Introspection

Cortex can automatically discover and analyze database schemas.

### Introspecting Tables

```python
from cortex.core.data.sources.service import DataSourceService

service = DataSourceService()

# Get all tables
tables = service.get_tables(data_source_id="source-123")

# Output:
# [
#   {"name": "customers", "row_count": 10000},
#   {"name": "orders", "row_count": 50000},
#   {"name": "products", "row_count": 500}
# ]
```

### Introspecting Columns

```python
# Get columns for a table
columns = service.get_columns(
    data_source_id="source-123",
    table_name="customers"
)

# Output:
# [
#   {"name": "id", "type": "integer", "nullable": false},
#   {"name": "email", "type": "varchar", "nullable": false},
#   {"name": "created_at", "type": "timestamp", "nullable": true}
# ]
```

### Humanized Schema Generation

Cortex can generate human-readable schema descriptions:

```python
schema = service.get_humanized_schema(
    data_source_id="source-123",
    table_name="customers"
)

# Output:
# {
#   "table": "customers",
#   "description": "Customer information table",
#   "columns": [
#     {
#       "name": "id",
#       "type": "integer",
#       "description": "Unique customer identifier",
#       "suggested_as": "dimension"
#     },
#     {
#       "name": "lifetime_value",
#       "type": "numeric",
#       "description": "Total customer value",
#       "suggested_as": "measure",
#       "suggested_aggregation": "sum"
#     }
#   ]
# }
```

This is particularly useful for:
- AI-powered metric generation
- Automated data model creation
- Schema documentation
- New user onboarding

## File Storage & Tiered Architecture

For file-based data sources (CSV, Google Sheets), Cortex uses a tiered storage architecture:

### Storage Tiers

1. **Input Storage**: Raw uploaded files
   - Local filesystem or GCS bucket
   - Original file format preserved
   
2. **SQLite Storage**: Converted databases
   - Permanent storage layer
   - Optimized for queries
   
3. **Cache Layer**: Recently accessed files
   - LRU cache with configurable size
   - Automatic eviction based on usage

### Configuration

```bash
# Local storage (default)
export CORTEX_FILE_STORAGE_TYPE=local
export CORTEX_FILE_STORAGE_INPUT_DIR=./.cortex/storage/inputs
export CORTEX_FILE_STORAGE_SQLITE_DIR=./.cortex/storage/sqlite

# Google Cloud Storage
export CORTEX_FILE_STORAGE_TYPE=gcs
export CORTEX_FILE_STORAGE_GCS_BUCKET=my-cortex-bucket
export CORTEX_FILE_STORAGE_GCS_PREFIX=cortex-files

# File Storage Cache settings
export CORTEX_FILE_STORAGE_CACHE_DIR=./.cortex/cache
export CORTEX_FILE_STORAGE_CACHE_MAX_SIZE_GB=10
export CORTEX_FILE_STORAGE_CACHE_TTL_HOURS=168  # 7 days
```

### Background Jobs

The cache manager runs as a background job (via Plombery):

- **Eviction Schedule**: Every 2 hours
- **LRU Strategy**: Least recently used files removed first
- **Size Monitoring**: Automatic cleanup when cache exceeds limit
- **Health Checks**: Verify cache integrity

## Adding Custom Connectors

Cortex uses an extensible factory pattern for data source connectors.

### 1. Create Connector Class

```python
from cortex.core.connectors.base import BaseConnector
from typing import Any, Dict, List

class MyCustomConnector(BaseConnector):
    """Connector for my custom data source."""
    
    def test_connection(self) -> bool:
        """Test if connection is working."""
        # Implementation
        pass
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        # Implementation
        pass
    
    def get_tables(self) -> List[str]:
        """Get list of available tables."""
        # Implementation
        pass
    
    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a table."""
        # Implementation
        pass
```

### 2. Register Connector

```python
from cortex.core.connectors.factory import ConnectorFactory

factory = ConnectorFactory()
factory.register_connector("my_custom_source", MyCustomConnector)
```

### 3. Use Connector

```json
{
  "name": "My Custom Source",
  "alias": "custom_src",
  "source_catalog": "database",
  "source_type": "my_custom_source",
  "config": {
    "custom_param": "value"
  }
}
```

## Best Practices

### Security

1. **Use Read-Only Credentials**: Create database users with SELECT-only permissions
2. **SSL/TLS Connections**: Enable encrypted connections when available
3. **Secrets Management**: Store credentials in environment variables or secret managers
4. **Network Security**: Use VPNs or private networks for database access

### Performance

1. **Index Key Columns**: Ensure filtered and grouped columns are indexed
2. **Partition Large Tables**: Use date-based partitioning for time-series data
3. **Monitor Connection Pools**: Watch for connection exhaustion
4. **Use Pre-aggregations**: Create rollups for frequently accessed data

### Reliability

1. **Test Connections**: Validate connections before creating data sources
2. **Monitor Health**: Set up alerts for connection failures
3. **Handle Timeouts**: Configure appropriate query timeouts
4. **Retry Logic**: Implement retries for transient failures

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to database

**Solutions:**
- Verify host, port, and credentials
- Check network connectivity
- Ensure database is running
- Verify firewall rules
- Check SSL/TLS requirements

### Performance Issues

**Problem**: Slow query execution

**Solutions:**
- Check database indexes
- Review query execution plans
- Enable query result caching
- Create pre-aggregations
- Optimize JOIN operations

### Schema Detection Issues

**Problem**: Tables or columns not detected

**Solutions:**
- Verify database permissions
- Check schema/dataset configuration
- Ensure tables are not system tables
- Refresh schema cache

## Related Documentation

- [Semantic Layer](../semantics/README.md) - Defining metrics on data sources
- [Query Engine](../query/README.md) - How queries are executed
- [Spreadsheet Configuration](../../connectors/api/sheets/README.md) - CSV and Google Sheets setup
- [API Reference](../../../api/README.md) - Data source management endpoints
- [Multi Tenancy](../../../docs/content/multi-tenancy.md) - Environment isolation
