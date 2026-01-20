# Multi Tenancy

Cortex provides a robust multi-tenant architecture that enables you to serve multiple organizations, teams, and users from a single installation while maintaining data isolation and security.

![Multi Tenancy Hierarchy](../assets/multi_tenancy_hierarchy.svg)

## Overview

The multi tenant system in Cortex is built on a three tier hierarchy:

**Workspaces → Environments → Consumers**

This structure provides:
- **Organizational Isolation**: Separate workspaces for different organizations or teams
- **Environment Segregation**: Dev/staging/production environments within workspaces
- **User Management**: Granular consumer-level access and personalization
- **Context-Aware Queries**: Automatic data filtering based on user context
- **Secure Data Access**: Each level enforces its own access controls

## Hierarchy Levels

### 1. Workspaces

Workspaces are the top-level organizational units, typically representing:
- Separate companies/organizations
-Different business units
- Independent teams or departments

**Workspace Properties:**
```json
{
  "id": "workspace-123",
  "name": "Acme Corporation",
  "description": "Main corporate workspace",
  "created_at": "2024-01-01T00:00:00Z",
  "settings": {
    "timezone": "America/New_York",
    "currency": "USD"
  }
}
```

**Use Cases:**
- SaaS multi-tenancy: One workspace per customer
- Enterprise deployments: One workspace per division
- Development teams: One workspace per project

### 2. Environments

Environments exist within workspaces and represent different development stages or deployment targets:

**Common environment types:**
- **Development**: For testing and development
- **Staging**: Pre-production testing
- **Production**: Live user-facing environment

**Environment Properties:**
```json
{
  "id": "env-456",
  "workspace_id": "workspace-123",
  "name": "Production",
  "description": "Production environment",
  "environment_type": "production",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Benefits:**
- Isolated data sources per environment
- Separate metrics and dashboards
- Environment-specific configurations
- Safe testing without affecting production

### 3. Consumers

Consumers represent end users who query data and view dashboards.

**Consumer Properties:**
```json
{
  "id": "consumer-789",
  "environment_id": "env-456",
  "name": "John Doe",
  "email": "john@example.com",
  "properties": {
    "department": "Sales",
    "region": "US-West",
    "role": "manager",
    "team_id": "team-123"
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Consumer properties enable:**
- Row-level security filtering
- Personalized dashboards
- Role-based metric access
- Context-aware data queries

## Consumer Groups

Consumer groups organize users with shared properties or access levels.

**Group Structure:**
```json
{
  "id": "group-101",
  "environment_id": "env-456",
  "name": "Sales Managers",
  "description": "All sales managers in US regions",
  "properties": {
    "department": "Sales",
    "role": "manager",
    "access_level": "manager"
  },
  "members": ["consumer-789", "consumer-790"]
}
```

**Common use cases:**
- Department-based groups
- Regional teams
- Role-based access control
- Feature access tiers (free, pro, enterprise)

## Context Aware Query Execution

Cortex automatically applies consumer context to queries for data personalization and security.

### How It Works

When a consumer executes a metric, Cortex:

1. **Retrieves Consumer Properties**: Load user properties and group memberships
2. **Applies Context Filters**: Automatically add filters based on properties
3. **Executes Query**: Run query with personalized filters
4. **Returns Results**: User sees only their authorized data

## Environment Level Isolation

Each environment maintains complete isolation:

### Isolated Resources

- **Data Sources**: Separate database connections per environment
- **Data Models**: Independent data model definitions
- **Metrics**: Environment-specific metrics
- **Dashboards**: Separate dashboard configurations
- **Consumers**: User lists scoped to environments
- **Cache**: Environment-namespaced cache keys
- **Query History**: Separate execution logs

### Benefits

1. **Safe Testing**: Test changes without affecting production
2. **Data Segregation**: Production data never mixes with dev/staging
3. **Independent Scaling**: Scale environments separately
4. **Configuration Flexibility**: Different settings per environment
5. **Regulatory Compliance**: Meet data residency requirements

## Creating Multi-Tenant Structures

### Create a Workspace

```python
import httpx

workspace = httpx.post("http://localhost:9002/api/v1/workspaces", json={
    "name": "Acme Corporation",
    "description": "Main corporate workspace",
    "settings": {
        "timezone": "America/New_York",
        "currency": "USD"
    }
}).json()
```

### Create Environments

```python
# Production environment
prod_env = httpx.post("http://localhost:9002/api/v1/environments", json={
    "workspace_id": workspace["id"],
    "name": "Production",
    "description": "Production environment",
    "environment_type": "production"
}).json()

# Development environment
dev_env = httpx.post("http://localhost:9002/api/v1/environments", json={
    "workspace_id": workspace["id"],
    "name": "Development",
    "description": "Development and testing",
    "environment_type": "development"
}).json()
```

### Create Consumers

```python
consumer = httpx.post("http://localhost:9002/api/v1/consumers", json={
    "environment_id": prod_env["id"],
    "name": "John Doe",
    "email": "john@example.com",
    "properties": {
        "department": "Sales",
        "region": "US-West",
        "role": "manager",
        "team_id": "team-123"
    }
}).json()
```

### Create Consumer Groups

```python
group = httpx.post("http://localhost:9002/api/v1/consumers/groups", json={
    "environment_id": prod_env["id"],
    "name": "Sales Managers",
    "description": "All sales managers",
    "properties": {
        "department": "Sales",
        "role": "manager"
    }
}).json()

# Add consumer to group
httpx.post(f"http://localhost:9002/api/v1/consumers/groups/{group['id']}/members", json={
    "consumer_id": consumer["id"]
})
```

## Security Considerations

### Authentication & Authorization

> [!WARNING]
> Authentication is not yet implemented. All endpoints are currently publicly accessible.

**Planned features:**
- JWT-based authentication
- Role-based access control (RBAC)
- API key management
- OAuth 2.0 integration

### Data Isolation

**Current safeguards:**
- Environment-scoped database queries
- Consumer context enforcement
- Workspace-level separation

**Best practices:**
1. Always use consumer context in queries
2. Validate environment IDs in requests
3. Implement row-level security with context filters
4. Audit access logs regularly

### Compliance

Multi-tenancy supports regulatory compliance:
- **GDPR**: Data residency via environment isolation
- **SOC 2**: Audit trails and access logs
- **HIPAA**: Environment-level data segregation
- **PCI DSS**: Workspace isolation for payment data

## Use Cases

### SaaS Application

```
Workspace: Customer A
├── Environment: Production
│   ├── Consumer: User 1 (properties: {customer_id: "A"})
│   └── Consumer: User 2 (properties: {customer_id: "A"})
└── Environment: Demo
    └── Consumer: Trial User

Workspace: Customer B
├── Environment: Production
│   ├── Consumer: User 3 (properties: {customer_id: "B"})
│   └── Consumer: User 4 (properties: {customer_id: "B"})
```

### Enterprise Deployment

```
Workspace: Global Corporation
├── Environment: Production
│   ├── Consumer Group: North America
│   │   └── Consumers with properties: {region: "NA"}
│   ├── Consumer Group: Europe
│   │   └── Consumers with properties: {region: "EU"}
│   └── Consumer Group: Asia
│       └── Consumers with properties: {region: "APAC"}
└── Environment: Staging
    └── Test users
```

### Multi-Team Development

```
Workspace: Engineering Team
├── Environment: Development
│   ├── Consumer: Developer 1
│   └── Consumer: Developer 2
├── Environment: Staging
│   ├── Consumer: QA Tester 1
│   └── Consumer: QA Tester 2
└── Environment: Production
    ├── Consumer Group: Product Managers
    └── Consumer Group: Executives
```

## API Reference

### Workspace Endpoints

- `GET /api/v1/workspaces` - List workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces/{id}` - Get workspace
- `PUT /api/v1/workspaces/{id}` - Update workspace
- `DELETE /api/v1/workspaces/{id}` - Delete workspace

### Environment Endpoints

- `GET /api/v1/environments` - List environments
- `POST /api/v1/environments` - Create environment
- `GET /api/v1/environments/{id}` - Get environment
- `PUT /api/v1/environments/{id}` - Update environment
- `DELETE /api/v1/environments/{id}` - Delete environment

### Consumer Endpoints

- `GET /api/v1/consumers` - List consumers
- `POST /api/v1/consumers` - Create consumer
- `GET /api/v1/consumers/{id}` - Get consumer
- `PUT /api/v1/consumers/{id}` - Update consumer
- `DELETE /api/v1/consumers/{id}` - Delete consumer

### Consumer Group Endpoints

- `GET /api/v1/consumers/groups` - List groups
- `POST /api/v1/consumers/groups` - Create group
- `GET /api/v1/consumers/groups/{id}` - Get group
- `PUT /api/v1/consumers/groups/{id}` - Update group
- `DELETE /api/v1/consumers/groups/{id}` - Delete group
- `POST /api/v1/consumers/groups/{id}/members` - Add member
- `DELETE /api/v1/consumers/groups/{id}/members/{consumer_id}` - Remove member

## Related Documentation

- [Getting Started](getting-started.md) - Initial workspace setup
- [Architecture](architecture.md) - Multi-tenant architecture details
- [Semantic Layer](../../core/semantics/README.md) - Context-aware metrics
- [API Reference](../../api/README.md) - Complete API documentation
