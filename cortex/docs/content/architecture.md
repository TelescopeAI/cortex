# Cortex Architecture

This document provides a high-level overview of the Cortex Headless BI platform architecture, explaining how the various components work together to deliver a modern, modular analytics solution.

![High-Level Architecture](../assets/high_level_architecture.png)
*Cortex high-level architecture diagram*

## Layers

Cortex follows a layered architecture pattern within a monorepo, ensuring modularity, ease of maintenance, and independent evolution of key components.

### 1. API Layer

**Technology**: FastAPI with Pydantic

**Responsibilities:**
- REST API endpoint creation and routing
- Request/response validation and serialization
- Auto-generated OpenAPI documentation
- CORS configuration
- Error handling and responses

**Key Features:**
- Type-safe request/response models
- Automatic OpenAPI/Swagger documentation
- Async request handling
- Dependency injection

### 2. Service Layer

**Location**: `cortex/core/services/`

**Responsibilities:**
- Business logic orchestration
- Cross-cutting concerns (logging, validation)
- Transaction management
- Service composition

**Key Services:**
- `DataSourceService` - Data source management
- `MetricService` - Metric creation and management
- `DashboardService` - Dashboard operations
- `QueryHistoryService` - Query analytics

### 3. Core Layer

The core layer contains the fundamental analytics capabilities:

#### Semantic Layer (`cortex/core/semantics/`)

> [!IMPORTANT]
> The semantic layer is the foundation of Cortex, providing a business-friendly abstraction over raw data.

- JSON-based metric definitions
- Measures, dimensions, filters, aggregations
- Output formatting (in-query and post-query)
- Parameter system for dynamic queries
- Validation and compilation pipeline

[📖 Read more about the Semantic Layer](../core/semantics/README.md)

#### Query Engine (`cortex/core/query/`)

- SQL generation from semantic definitions
- Multi-database support
- Multi-layer caching (Redis, in-memory)
- Pre-aggregation and rollup tables
- Query history and performance tracking

[📖 Read more about the Query Engine](../core/query/README.md)

#### Dashboard Engine (`cortex/core/dashboards/`)

- Multi-view dashboard system
- 10+ visualization types
- Embedded metrics
- Real-time preview
- Field mapping and transformations

[📖 Read more about Dashboards](../core/dashboards/README.md)

### 4. Connector Layer

**Location**: `cortex/core/connectors/`

**Responsibilities:**
- Database connection management
- Query execution across data sources
- Schema introspection
- Connection pooling

**Supported Connectors:**
- PostgreSQL
- MySQL
- BigQuery
- SQLite
- Spreadsheets (CSV, Google Sheets)

[📖 Read more about Data Sources](../core/data/sources/README.md)

### 5. Storage Layer

**Location**: `cortex/core/storage/`

**Responsibilities:**
- Cortex metadata storage (workspaces, metrics, dashboards)
- Database-agnostic storage with SQLAlchemy
- Migration management with Alembic

**Storage Models:**
- Workspaces and Environments
- Data sources and models
- Metrics and dashboards
- Consumers and consumer groups
- Query history

### 6. Jobs Server

**Location**: `cortex/jobs/`

**Technology**: Plombery task scheduler

**Responsibilities:**
- Background task execution
- Scheduled jobs (cache eviction, pre-aggregation refresh)
- File storage management
- Independent scaling from API server

**Key Jobs:**
- SQLite cache eviction (every 2 hours)
- Pre-aggregation refresh
- Data source health checks

### Typical Request Flow

1. **Client Request**: User requests metric execution via API
2. **API Validation**: FastAPI validates request schema
3. **Service Layer**: MetricService orchestrates execution
4. **Semantic Parsing**: SemanticMetric parsed and validated
5. **Cache Check**: Query engine checks cache for results
6. **SQL Generation**: If cache miss, generate SQL from semantic definition
7. **Query Execution**: Execute query via appropriate connector
8. **Result Formatting**: Apply post-query transformations
9. **Cache Storage**: Store results in cache
10. **API Response**: Return formatted results to client

## AI Agent Integration Points

The Cortex architecture is designed with AI agent integration in mind:

### 1. Natural Language Interface

**Integration Point**: Semantic Layer

AI agents can translate natural language questions into `SemanticMetric` instances:

```python
# User asks: "What was our revenue last month?"
# AI agent generates:
{
  "name": "last_month_revenue",
  "measures": [{"name": "revenue", "type": "sum", "query": "amount"}],
  "filters": [{
    "query": "date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')"
  }]
}
```

### 2. Intelligent Discovery

**Integration Point**: Semantic Search

AI agents can search and recommend metrics based on:
- User query semantics
- Historical query patterns
- Consumer context
- Business domain

### 3. Automated Modeling

**Integration Point**: Schema Introspection

AI agents can generate data models from schema analysis:
- Detect table relationships
- Suggest appropriate measures
- Recommend dimensions
- Propose filters

### 4. Context Personalization

**Integration Point**: Consumer Properties

AI agents leverage consumer properties for:
- Role-based metric suggestions
- Personalized dashboards
- Context-aware filters
- Custom aggregations

### 5. Performance Optimization

**Integration Point**: Query History

AI agents analyze query patterns to:
- Suggest pre-aggregations
- Optimize cache TTLs
- Identify slow queries
- Recommend indexes

### 6. Quality Monitoring

**Integration Point**: Execution Logs

AI agents monitor data quality through:
- Anomaly detection
- Trend analysis
- Data freshness checks
- Error pattern identification

## Monorepo Structure

```
cortex/
├── cortex/                   # Core Python package
│   ├── api/                  # FastAPI REST API
│   │   ├── routers/          # API endpoint routers
│   │   ├── schemas/          # Request/response schemas
│   │   └── main.py           # API application entry point
│   ├── core/                 # Core business logic
│   │   ├── cache/            # Caching implementations
│   │   ├── connectors/       # Database connectors
│   │   ├── consumers/        # Consumer management
│   │   ├── dashboards/       # Dashboard engine
│   │   ├── data/             # Data models and sources
│   │   ├── onboarding/       # Setup automation
│   │   ├── preaggregations/  # Pre-aggregation system
│   │   ├── query/            # Query engine
│   │   ├── semantics/        # Semantic layer
│   │   ├── services/         # Business services
│   │   ├── storage/          # Database models
│   │   └── workspaces/       # Multi-tenancy
│   ├── jobs/                 # Background jobs server
│   │   ├── cache/            # Cache management
│   │   ├── tasks/            # Scheduled tasks
│   │   ├── registry.py       # Job registration
│   │   └── server.py         # Jobs server launcher
│   ├── migrations/           # Alembic migrations
│   ├── app.py                # Unified launcher
│   └── __main__.py           # CLI entry point
├── frontend/cortex/          # Nuxt admin interface
│   ├── app/                  # Nuxt application
│   │   ├── components/       # Vue components
│   │   ├── composables/      # Composable functions
│   │   ├── pages/            # Page components
│   │   └── types/            # TypeScript types
│   └── nuxt.config.ts        # Nuxt configuration
└── pyproject.toml            # Poetry dependencies
```

## Deployment Architecture

### Development

```
┌─────────────────┐
│ Unified Launcher│
│  (API + Jobs)   │
│   Port: 9002    │
└─────────────────┘
        │
        ├─> API Server (FastAPI)
        └─> Jobs Server (Plombery)
```

### Production

```
┌──────────────┐        ┌──────────────┐
│      API     │        │     Jobs     │
│  Port: 9002  │        │  Port: 9003  │
└──────────────┘        └──────────────┘
      │                        │
      ├─> Metadata DB   <──────┤
      ├─> Redis Cache   <──────┤
      └─> Files Storage <──────┘
```

**Horizontal Scaling:**
- API servers can be scaled horizontally behind a load balancer
- Jobs server runs as single instance (managed by scheduler)
- Shared Redis cache across API instances
- Shared PostgreSQL for metadata
- Shared GCS/S3 for file storage

## Stack

### Backend

- **Language**: Python 3.12+
- **Web Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Validation**: Pydantic
- **Task Scheduler**: Plombery
- **Caching**: Redis / In-Memory
- **API Docs**: Scalar FastAPI

### Frontend

- **Framework**: Nuxt 4
- **Language**: TypeScript
- **UI Components**: Vue ShadCN
- **Charts**: ECharts

### Infrastructure

- **Databases**: PostgreSQL (metadata), Redis (cache)
- **File Storage**: Local filesystem, Google Cloud Storage
- **Deployment**: Docker, kubernetes (planned)

## Security Considerations

> [!WARNING]
> Authentication is not yet implemented. All endpoints are currently publicly accessible.

**Planned security features:**
- JWT-based authentication
- Role-based access control (RBAC)
- API key management
- Rate limiting
- SQL injection prevention (via parameterized queries)
- Encrypted credentials storage
- Audit logging

## Performance

### Caching Strategy

- **L1 Cache**: In-memory (process-local, development)
- **L2 Cache**: Redis (distributed, production)
- **L3 Cache**: Pre-aggregation tables (query results)

### Scalability

**Vertical:**
- API server CPU/memory
- Database connections pool size
- Cache size

**Horizontal:**
- Multiple API server instances
- Load balancer distribution
- Shared cache and storage

## Related Documentation

- [Getting Started](getting-started.md) - Setup and installation
- [Multi Tenancy](multi-tenancy.md) - Workspaces and environments
- [Development](development.md) - Contributing and development workflow
- [API Reference](../api/README.md) - REST API documentation
