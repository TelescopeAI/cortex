# Cortex Headless BI

## Lightweight Modular Analytics Platform

A modular, lightweight analytics engine built in Python to power customer-facing analytics applications. The platform provides a unified semantic layer for defining business data models, a dynamic query engine that integrates with heterogeneous data sources, and a robust user management and authorization system—all accessible via a FastAPI-powered REST API. The semantic layer is designed to support advanced AI agent integration for intelligent analytics, natural language querying, and automated insights generation.

![Cortex Dashboard](cortex/docs/assets/cortex_hero.png)

## Overview

This platform is designed to abstract complex data sources into a business-friendly semantic layer. It enables developers to define data models in JSON (with YAML support planned), dynamically generate queries across multiple data sources, and securely expose analytics functionality to both admin/developer users and end users.

### Key Features

- **Semantic Layer**
  - Define and manage data models in JSON with measures, dimensions, filters, and aggregations
  - Dynamic context aware schema generation
  - Conditional logic support for dynamic column combinations
  - Versioning and audit trails for metrics and data models
  - Parameter system for dynamic query generation
  - Automated metric discovery and recommendations from database schemas
  - Metric preview mode for validation before saving

- **Query Engine**
  - Translates semantic definitions into optimized queries
  - Real-time output formatting during query execution and post-processing
  - Multi-layer caching with Redis and in-memory backends
  - Planned support for multi-source queries (PostgreSQL, MySQL, BigQuery, SQLite)
  - Pre-aggregations and rollup tables for performance optimization
  - Query bindings for automatic rollup table utilization

- **Data Source Integration**
  - PostgreSQL, MySQL, BigQuery with persistent connectors
  - SQLite for in-memory analytics
  - Spreadsheet support (CSV, Google Sheets) - see [Spreadsheet Configuration](cortex/core/connectors/api/sheets/README.md)
  - Extensible factory pattern for adding new data sources
  - Schema introspection and humanized schema generation

- **Background Jobs & Scalable Storage**
  - Tiered storage architecture: Local filesystem, Google Cloud Storage (GCS), S3 (planned)
  - Automatic LRU cache management for SQLite databases (10GB default, configurable)
  - Scheduled cache eviction every 2 hours via Plombery job scheduler
  - Separate API and Jobs server processes for independent scaling
  - Unified launcher or separate service deployment modes

- **Dashboard & Visualization Engine**
  - Multi-view dashboard system with executive, operational, and tactical types
  - Support for 10+ visualization types: single value, gauge, bar/line/area/pie/donut charts, scatter plots, heatmaps, and tables
  - Advanced chart features with ECharts integration
  - Field mapping and data transformation for visualizations
  - Widget-level metric execution with override support
  - Embedded metrics: Define metrics directly within dashboard widgets without saving them first
  - Dashboard preview with real-time metric execution

- **Multi-Tenancy**
  - Hierarchical organization: Workspaces → Environments → Consumers
  - Consumer groups for organizing users with shared properties
  - Environment-level isolation for dev/staging/production
  - Context-aware query execution based on consumer properties

- **API-First Approach**
  - All functionality exposed via FastAPI-based REST endpoints
  - Auto-generated OpenAPI documentation with Scalar FastAPI
  - Comprehensive request/response validation with Pydantic

- **Query History & Monitoring**
  - Automatic logging of all query executions
  - Query performance analytics and slow query identification
  - Cache hit rate tracking and statistics
  - Execution history with filtering and search capabilities

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL (or other supported database)

### Installation

#### Production Installation (Recommended)
```bash
# Install core package
pip install telescope-cortex

# Install with API extras
pip install telescope-cortex[api]

# Install with GCS support (for cloud file storage)
pip install telescope-cortex[api,gcloud]

# Set up environment variables
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
# Configure your database settings (see Environment Configuration below)

# Start the API server
python -m cortex
```

#### Local Development Installation
```bash
# Clone the repository
git clone https://github.com/TelescopeAI/cortex
cd cortex

# Install core dependencies only
poetry install --only main

# Install with all dependencies including FastAPI
poetry install --with api

# Install with GCS support (for cloud file storage)
poetry install --with api --extras gcloud

# Set up environment variables
cp local.env .env
# Edit .env with your configuration

# Enable auto-migration for development
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true

# Start the unified app launcher (API + Jobs server)
poetry run python -m cortex

# OR start just the API server
poetry run python -m cortex.api

# OR start just the Jobs server
poetry run python -m cortex.jobs
```

#### Database Migrations & Onboarding

The platform includes an automated onboarding system that handles initial setup:

- **Automatic Migrations**: Database migrations are automatically applied on startup (when enabled)
- **Default Workspace & Environment**: Creates default workspace and test environment if none exist
- **Default Data Model**: Automatically creates a default data model in the first available environment

Set the following environment variable to enable auto-migration:

```bash
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
```

For more information on running migrations manually or troubleshooting migration issues, see the [Database Migrations Guide](cortex/migrations/MIGRATION_GUIDE.md).

#### Environment Configuration

Cortex uses `python-dotenv` to automatically load environment variables from `.env` files. This means you no longer need to manually source environment variables!

**How it works:**
1. Creates `local.env` in the project root with your configuration
2. When you run the application, the environment variables are automatically loaded from `local.env`
3. You can also specify a custom env file path using the `CORTEX_ENV_FILE_PATH` environment variable

**Example local.env file:**
```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://cortex.web.local,https://cortex.web.local

# Execution Environment
EXECUTION_ENV=local

# Database configuration
CORTEX_DB_TYPE=postgresql  # postgresql, mysql, sqlite
CORTEX_DB_HOST=localhost
CORTEX_DB_PORT=5432
CORTEX_DB_NAME=cortex
CORTEX_DB_USERNAME=root
CORTEX_DB_PASSWORD=password

# Auto-migrations
CORTEX_AUTO_APPLY_DB_MIGRATIONS=true

# SQLite (only if CORTEX_DB_TYPE=sqlite)
# CORTEX_DB_FILE=./cortex.db
# CORTEX_DB_MEMORY=false

# Cache configuration
CORTEX_CACHE_ENABLED=true
CORTEX_CACHE_BACKEND=redis  # redis or memory
CORTEX_CACHE_REDIS_URL=redis://localhost:6379

# Pre-aggregations
CORTEX_PREAGGREGATIONS_ENABLED=false

# API configuration
API_BASE_URL=http://localhost:9002

# File Storage & Spreadsheet Configuration
CORTEX_FILE_STORAGE_TYPE=local  # or 'gcs' for Google Cloud Storage
CORTEX_FILE_STORAGE_INPUT_DIR=./.cortex/storage/inputs
CORTEX_FILE_STORAGE_SQLITE_DIR=./.cortex/storage/sqlite
CORTEX_FILE_STORAGE_CACHE_DIR=./.cortex/cache/sqlite
CORTEX_FILE_STORAGE_CACHE_MAX_SIZE_GB=10

# GCS Configuration (only if CORTEX_FILE_STORAGE_TYPE=gcs)
CORTEX_FILE_STORAGE_GCS_BUCKET=my-cortex-bucket
CORTEX_FILE_STORAGE_GCS_PREFIX=cortex-files

# Jobs Server Configuration
CORTEX_ENABLE_JOBS=true  # Enable background jobs (auto-enabled for GCS)
CORTEX_API_HOST=0.0.0.0
CORTEX_API_PORT=9002
CORTEX_JOBS_HOST=0.0.0.0
CORTEX_JOBS_PORT=9003
```

**Using a custom env file:**
```bash
# Use a specific env file
CORTEX_ENV_FILE_PATH=/path/to/custom.env poetry run uvicorn cortex.api.main:app --reload

# Or export for the shell session
export CORTEX_ENV_FILE_PATH="$HOME/.cortex/dev.env"
poetry run uvicorn cortex.api.main:app --reload
```

**Using Docker:**
```yaml
# docker-compose.yml
services:
  server:
    env_file:
      - ./local.docker.env
```

**Required environment variables:**
- `CORTEX_DB_TYPE` - Database type (postgresql, mysql, sqlite, duckdb)
- `CORTEX_DB_HOST` - Database host (unless using SQLite)
- `CORTEX_DB_PORT` - Database port (unless using SQLite)
- `CORTEX_DB_NAME` - Database name
- `CORTEX_DB_USERNAME` - Database username (unless using SQLite)
- `CORTEX_DB_PASSWORD` - Database password (unless using SQLite)
- `EXECUTION_ENV` - Execution environment (local, dev, staging, production)

#### Database Migrations

Cortex uses **Alembic** for database schema management with support for multiple databases (PostgreSQL, MySQL, SQLite).

**Key Features:**
- **Database-Specific Migrations**: Each database type maintains its own migration chain for optimal compatibility
- **Automatic Initialization**: Generates initial migration if none exist for the database type
- **Interactive Safety**: Shows migration plan with confirmation before applying
- **Environment Variable Control**: Full customization via `CORTEX_*` environment variables
- **Custom Directories**: Support for application-specific migration folders

**Migration Architecture**

Migrations are organized by database type to avoid compatibility issues:

```
cortex/migrations/alembic/versions/
├── sqlite/
│   └── [migration files for SQLite]
├── postgresql/
│   └── [migration files for PostgreSQL]
└── mysql/
    └── [migration files for MySQL]
```

**Quick Start**

Enable automatic migrations on startup:

```bash
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
python -m cortex.api
```

You'll see an interactive plan and confirmation before migrations are applied.

**Environment Variables**

```bash
# Enable/disable automatic migration on startup (default: true)
export CORTEX_AUTO_APPLY_DB_MIGRATIONS="true"

# Interactive confirmation before applying (default: true on TTY)
export CORTEX_DB_MIGRATIONS_IS_INTERACTIVE="true"

# Custom migration directory (optional)
export CORTEX_MIGRATIONS_VERSIONS_DIRECTORY="/path/to/migrations"

# Custom environment file (optional)
export CORTEX_ENV_FILE_PATH="/path/to/.env.custom"
```

**Manual Migration**

Run Alembic commands directly:

```bash
cd cortex

# Ensure database type is set
export CORTEX_DB_TYPE=sqlite

# Apply all pending migrations
alembic upgrade head

# View migration history
alembic history --verbose

# Get current revision
alembic current
```

**For Complete Documentation**

See the [Database Migrations Guide](cortex/migrations/MIGRATION_GUIDE.md) for:
- Detailed configuration and usage
- Auto-generation of initial migrations
- Custom migration directories
- Migration file format and best practices
- Troubleshooting and performance considerations
- Security and audit considerations

### Starting the Application

#### Using the Unified Launcher (Recommended for Development)

The unified launcher starts both the API and Jobs servers for you:

```bash
# Start both API and Jobs servers
python -m cortex

# Start only API server (default)
python -m cortex

# Start only Jobs server
python -m cortex.jobs

# Enable jobs explicitly
CORTEX_ENABLE_JOBS=true python -m cortex

# Auto-enable jobs with GCS storage
CORTEX_FILE_STORAGE_TYPE=gcs python -m cortex
```

#### Production Deployment (Separate Services)

For production, deploy each server separately for independent scaling:

```bash
# Terminal 1: Start API server
python -m cortex.api

# Terminal 2: Start Jobs server
CORTEX_ENABLE_JOBS=true python -m cortex.jobs
```

#### File Storage Configuration

Configure where uploaded files and SQLite databases are stored:

```bash
# Local storage (default)
export CORTEX_FILE_STORAGE_TYPE=local
export CORTEX_FILE_STORAGE_INPUT_DIR=./.cortex/storage/inputs
export CORTEX_FILE_STORAGE_SQLITE_DIR=./.cortex/storage/sqlite

# Google Cloud Storage
export CORTEX_FILE_STORAGE_TYPE=gcs
export CORTEX_FILE_STORAGE_GCS_BUCKET=my-cortex-bucket
export CORTEX_FILE_STORAGE_GCS_PREFIX=cortex-files

# Cache configuration
export CORTEX_FILE_STORAGE_CACHE_DIR=./.cortex/cache/sqlite
export CORTEX_FILE_STORAGE_CACHE_MAX_SIZE_GB=10
export CORTEX_FILE_STORAGE_CACHE_TTL_HOURS=168
```

For more details, see [Spreadsheet Data Sources Configuration](cortex/core/connectors/api/sheets/README.md).

### Quick Start - Creating Your First Semantic Model

1. **Define a Data Source**:
```json
{
  "name": "sales_db",
  "source_type": "postgresql",
  "config": {
    "host": "localhost",
    "database": "sales",
    "username": "user",
    "password": "password"
  }
}
```

2. **Create a Semantic Metric with Output Formatting**:
```json
{
  "name": "monthly_revenue",
  "description": "Total revenue aggregated by month",
  "table_name": "sales",
  "measures": [
    {
      "name": "revenue",
      "type": "sum",
      "query": "amount",
      "formatting": [
        {
          "name": "currency_format",
          "type": "format",
          "mode": "post_query",
          "format_string": "${:,.2f}"
        }
      ]
    }
  ],
  "dimensions": [
    {
      "name": "month",
      "query": "sale_date",
      "formatting": [
        {
          "name": "date_format",
          "type": "cast",
          "mode": "in_query",
          "target_type": "date"
        }
      ]
    }
  ]
}
```

3. **Execute Queries**:
```python
from cortex.core.query.executor import QueryExecutor
from cortex.core.semantics.metrics.metric import SemanticMetric

executor = QueryExecutor()
result = executor.execute_metric(
    metric=your_metric,
    data_model=your_model,
    parameters={"start_date": "2024-01-01"}
)
```

## Studio

The platform includes a modern Vue.js frontend built with Nuxt 4 and TypeScript for creating and managing dashboards, metrics, and data visualizations.

### Features
- **Workspace & Environment Management**: Multi-tenant workspace management with environment isolation
- **Data Source Configuration**: Visual interface for connecting and configuring data sources
- **Data Model Builder**: Create and manage data models with schema introspection
- **Metric Builder**: Visual interface for creating semantic metrics with measures, dimensions, filters, and aggregations
  - Metric preview mode to validate definitions before saving
  - Automated metric recommendations from database schemas
- **Dashboard Builder**: Create multi-view dashboards with drag-and-drop widget placement
  - Embedded metrics: Define metrics directly in dashboard widgets
- **Visualization Editor**: Configure 10+ chart types with advanced field mapping
- **Consumer & Group Management**: Manage end users and consumer groups
- **Query History**: View and analyze query execution history and performance
- **Pre-aggregation Management**: Configure and monitor rollup tables
- **Real-time Preview**: Instant visualization of metric results during development

## Architecture

The project follows a layered architecture within a monorepo, ensuring modularity, ease of maintenance, and independent evolution of key components.

### Semantic Layer

This semantic layer is designed with AI agent integration in mind, providing:

- **Structured Semantic Models**: JSON-based metric definitions with measures, dimensions, joins, and aggregations
- **Advanced Output Formatting**: Support for data transformations at both query time (IN_QUERY) and post-execution (POST_QUERY)
- **Context-Aware Execution**: Consumer properties and environment isolation for personalized data access
- **Query Abstraction**: Database-agnostic query generation from semantic definitions
- **Execution Logging**: Comprehensive query execution logs for AI training and optimization
- **Parameter System**: Dynamic parameter substitution for flexible query generation
- **Validation Pipeline**: Automated validation and compilation of semantic models

This foundation will enable AI agents to:
- Translate natural language queries into semantic metric definitions
- Recommend relevant metrics and dimensions based on user context
- Optimize query performance through pattern analysis
- Generate automated insights and anomaly detection
- Learn from user behavior and query patterns for continuous improvement

### AI Agent Integration Points

1. **Natural Language Interface**: Convert user questions into `SemanticMetric` instances
2. **Intelligent Discovery**: Semantic search and recommendation across available metrics
3. **Automated Modeling**: AI-powered generation of data models from schema analysis
4. **Context Personalization**: Leverage consumer properties for role-based suggestions
5. **Performance Optimization**: Query pattern analysis and optimization recommendations
6. **Quality Monitoring**: Automated data quality assessment and anomaly detection


### Setup
```bash
cd frontend/cortex
yarn install

# Development mode
yarn run dev

# Production build
yarn run build
```

## API Reference

The platform provides a comprehensive REST API for all operations. Access the interactive API documentation at:
- **API Docs**: `http://localhost:9002/docs`
- **Classic UI**: `http://localhost:9002/docs/classic`
- **ReDoc UI**: `http://localhost:9002/redoc`

### Core API Endpoints

| Resource | Endpoint | Description |
|----------|----------|-------------|
| **Workspaces** | `/api/v1/workspaces` | Top-level organizational units |
| **Environments** | `/api/v1/environments` | Development stages within workspaces |
| **Data Sources** | `/api/v1/data/sources` | Database connection management |
| **Data Models** | `/api/v1/data/models` | Business data model definitions |
| **Metrics** | `/api/v1/metrics` | Semantic metric creation and execution |
| **Dashboards** | `/api/v1/dashboards` | Dashboard and widget management |
| **Consumers** | `/api/v1/consumers` | End user management |
| **Consumer Groups** | `/api/v1/consumers/groups` | User group management |
| **Query History** | `/api/v1/query/history` | Query execution logs and analytics |
| **Pre-aggregations** | `/api/v1/pre-aggregations` | Rollup table management |

### Example API Usage

```python
import httpx

# Create a workspace
response = httpx.post("http://localhost:9002/api/v1/workspaces", json={
    "name": "My Workspace",
    "description": "Production workspace"
})
workspace_id = response.json()["id"]

# Create an environment
response = httpx.post("http://localhost:9002/api/v1/environments", json={
    "workspace_id": workspace_id,
    "name": "Production",
    "description": "Production environment"
})
environment_id = response.json()["id"]

# Create a data source
response = httpx.post("http://localhost:9002/api/v1/data/sources", json={
    "environment_id": environment_id,
    "name": "Sales Database",
    "alias": "sales_db",
    "source_catalog": "database",
    "source_type": "postgresql",
    "config": {
        "host": "localhost",
        "port": 5432,
        "database": "sales",
        "username": "user",
        "password": "password"
    }
})

# Execute a metric
response = httpx.post(f"http://localhost:9002/api/v1/metrics/{metric_id}/execute", json={
    "parameters": {"start_date": "2024-01-01"},
    "cache": {"enabled": true, "ttl": 3600}
})
```

## Development

### Project Structure
```
cortex/
├── cortex/                   # Core Python package
│   ├── api/                  # FastAPI REST API (optional)
│   │   ├── routers/          # API endpoint routers
│   │   ├── schemas/          # Request/response schemas
│   │   └── main.py           # API application
│   ├── core/                 # Core semantic layer and query engine
│   │   ├── cache/            # Caching implementations
│   │   ├── connectors/       # Database connectors
│   │   ├── consumers/        # User management
│   │   ├── dashboards/       # Dashboard engine
│   │   ├── data/             # Data models and sources
│   │   ├── onboarding/       # Onboarding and setup automation
│   │   ├── preaggregations/  # Pre-aggregation system
│   │   ├── query/            # Query engine
│   │   ├── semantics/        # Semantic layer
│   │   ├── services/         # Business logic services
│   │   ├── storage/          # Database storage
│   │   └── workspaces/       # Multi-tenancy
│   ├── jobs/                 # Background jobs and task scheduling
│   │   ├── cache/            # Cache management for file storage
│   │   │   └── manager.py    # LRU cache manager with GCS backing
│   │   ├── tasks/            # Scheduled tasks
│   │   │   └── cache_eviction.py  # Cache eviction task (every 2 hours)
│   │   ├── registry.py       # Plombery pipeline registration
│   │   ├── server.py         # Jobs server launcher
│   │   └── __main__.py       # Direct jobs server entry point
│   ├── app.py                # Unified app launcher (API + Jobs)
│   ├── __main__.py           # Top-level entry point
│   └── migrations/           # Alembic database migrations
│       ├── alembic/          # Alembic configuration
│       │   ├── versions/     # Migration files
│       │   │   ├── sqlite/   # SQLite-specific migrations
│       │   │   ├── postgresql/ # PostgreSQL-specific migrations
│       │   │   └── mysql/    # MySQL-specific migrations
│       │   ├── env.py        # Alembic environment configuration
│       │   └── script.py.mako # Migration script template
│       ├── alembic.ini       # Alembic configuration file
│       └── MIGRATION_GUIDE.md # Database migrations guide
├── frontend/cortex/          # Nuxt admin interface
│   ├── app/                  # Application code
│   │   ├── components/       # Vue components
│   │   ├── composables/      # Composable functions
│   │   ├── pages/            # Page components
│   │   └── types/            # TypeScript types
└── pyproject.toml            # Poetry configuration
```

### Key Components

#### Backend
- **Semantic Layer**: Core data modeling with measures, dimensions, filters, and aggregations
- **Query Engine**: Database-agnostic SQL generation and execution
- **Cache Manager**: Multi-backend caching with Redis and in-memory support
- **Pre-aggregation Service**: Rollup table management and query optimization
- **Dashboard Engine**: Widget execution and visualization data processing
- **Consumer Management**: Multi-tenant user and group management
- **Query History**: Execution logging and performance analytics

#### Frontend
- **Workspace Management**: Multi-tenant workspace and environment configuration
- **Data Source Configurator**: Visual database connection setup
- **Metric Builder**: Drag-and-drop semantic metric creation
- **Dashboard Designer**: Multi-view dashboard builder with widget library
- **Query Explorer**: Query history and performance monitoring
- **User Management**: Consumer and group administration


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Attribution

Cortex was heavily inspired by [Cube's Semantic Layer](https://cube.dev) and [Metabase](https://metabase.com). We built upon their excellent work to create a lightweight, Python-focused analytics platform that integrates seamlessly with modern data stacks.

## Contributions

Contributions are welcome! Please feel free to submit a [Pull Request](https://github.com/TelescopeAI/cortex/compare).

## Support

For questions and support:
- [Open an issue on GitHub](https://github.com/TelescopeAI/cortex/issues)
- Email: [help@jointelescope.com](mailto:help@jointelescope.com)
- Documentation: [docs.jointelescope.com](https://docs.jointelescope.com)
- [Database Migrations Guide](cortex/migrations/MIGRATION_GUIDE.md)
- [Spreadsheet Data Sources Configuration](cortex/core/connectors/api/sheets/README.md)

## Roadmap

Upcoming features and completed items:

**Completed:**
- [x] File-based data sources (CSV, Excel, Google Sheets) - [Configuration Guide](cortex/core/connectors/api/sheets/README.md)
- [x] Tiered storage architecture (Local, GCS, S3-ready)
- [x] Background jobs and cache management via Plombery

**Planned:**
- [ ] Advanced AI agent integration
- [ ] Natural language query interface
- [ ] User authentication and authorization system
- [ ] Embedded analytics SDK
- [ ] Mobile-responsive dashboard views
- [ ] Multi-database joins
- [ ] S3 storage backend support

