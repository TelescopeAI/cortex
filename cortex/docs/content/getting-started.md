# Getting Started

This guide will walk you through installing and configuring Cortex, from initial setup to creating your first semantic model.

## Prerequisites

Before installing Cortex, ensure you have:

- **Python 3.12+** installed
- **PostgreSQL** (or other supported database) running
- **Redis** (optional, for caching)
- **Git** (for development installation)

## Installation

### Production Installation (Recommended)

For production deployments, install Cortex via pip:

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

### Local Development Installation

For local development, clone the repository and use Poetry:

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

## Database Migrations & Onboarding

Cortex includes an automated onboarding system that handles initial setup:

- **Automatic Migrations**: Database migrations are automatically applied on startup (when enabled)
- **Default Workspace & Environment**: Creates default workspace and test environment if none exist
- **Default Data Model**: Automatically creates a default data model in the first available environment

### Enable Auto-Migration

```bash
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
```

### Migration Architecture

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

### Manual Migration

Run Alembic commands directly:

```bash
cd cortex

# Ensure database type is set
export CORTEX_DB_TYPE=postgresql

# Apply all pending migrations
alembic upgrade head

# View migration history
alembic history --verbose

# Get current revision
alembic current
```

### Migration Environment Variables

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

**For complete migration documentation**, see the [Database Migrations Guide](../../migrations/MIGRATION_GUIDE.md).

## Environment Configuration

Cortex uses `python-dotenv` to automatically load environment variables from `.env` files.

### How It Works

1. Create `local.env` in the project root with your configuration
2. When you run the application, environment variables are automatically loaded from `local.env`
3. You can specify a custom env file path using the `CORTEX_ENV_FILE_PATH` environment variable

### Example local.env File

```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

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
CORTEX_FILE_STORAGE_INPUT_DIR=./.cortex/storage/inputs  # Uploaded CSV/Excel files
CORTEX_FILE_STORAGE_SQLITE_DIR=./.cortex/storage/sqlite  # Converted SQLite databases
CORTEX_FILE_STORAGE_CACHE_DIR=./.cortex/cache  # Cache metadata (file_storage_meta.db)
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

### Required Environment Variables

- `CORTEX_DB_TYPE` - Database type (postgresql, mysql, sqlite, duckdb)
- `CORTEX_DB_HOST` - Database host (unless using SQLite)
- `CORTEX_DB_PORT` - Database port (unless using SQLite)
- `CORTEX_DB_NAME` - Database name
- `CORTEX_DB_USERNAME` - Database username (unless using SQLite)
- `CORTEX_DB_PASSWORD` - Database password (unless using SQLite)
- `EXECUTION_ENV` - Execution environment (local, dev, staging, production)

### Using Custom Env Files

```bash
# Use a specific env file
CORTEX_ENV_FILE_PATH=/path/to/custom.env poetry run python -m cortex

# Or export for the shell session
export CORTEX_ENV_FILE_PATH="$HOME/.cortex/dev.env"
poetry run python -m cortex
```

### Using Docker

```yaml
# docker-compose.yml
services:
  server:
    env_file:
      - ./local.docker.env
```

## Starting the Application

### Using the Unified Launcher (Recommended for Development)

The unified launcher starts both the API and Jobs servers:

```bash
# Start both API and Jobs servers
python -m cortex

# Enable jobs explicitly
CORTEX_ENABLE_JOBS=true python -m cortex

# Auto-enable jobs with GCS storage
CORTEX_FILE_STORAGE_TYPE=gcs python -m cortex
```

### Production Deployment (Separate Services)

For production, deploy each server separately for independent scaling:

```bash
# Terminal 1: Start API server
python -m cortex.api

# Terminal 2: Start Jobs server
CORTEX_ENABLE_JOBS=true python -m cortex.jobs
```

**Access the API:**
- API Server: `http://localhost:9002`
- Jobs Server: `http://localhost:9003`
- API Documentation: `http://localhost:9002/docs`

## File Storage Configuration

Configure where uploaded files and SQLite databases are stored:

### Local Storage (Default)

```bash
export CORTEX_FILE_STORAGE_TYPE=local
export CORTEX_FILE_STORAGE_INPUT_DIR=./.cortex/storage/inputs
export CORTEX_FILE_STORAGE_SQLITE_DIR=./.cortex/storage/sqlite
```

### Google Cloud Storage

```bash
export CORTEX_FILE_STORAGE_TYPE=gcs
export CORTEX_FILE_STORAGE_GCS_BUCKET=my-cortex-bucket
export CORTEX_FILE_STORAGE_GCS_PREFIX=cortex-files
```

### Cache Configuration

```bash
export CORTEX_FILE_STORAGE_CACHE_DIR=./.cortex/cache  # Stores file_storage_meta.db
export CORTEX_FILE_STORAGE_CACHE_MAX_SIZE_GB=10
export CORTEX_FILE_STORAGE_CACHE_TTL_HOURS=168  # 7 days
```

For more details, see [Spreadsheet Data Sources Configuration](../../core/connectors/api/sheets/README.md).

## Quick Start Tutorial

### Step 1: Create a Workspace

```bash
curl -X POST http://localhost:9002/api/v1/workspaces \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Workspace",
    "description": "Production workspace"
  }'
```

### Step 2: Create an Environment

```bash
curl -X POST http://localhost:9002/api/v1/environments \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "workspace-id-from-step-1",
    "name": "Production",
    "description": "Production environment"
  }'
```

### Step 3: Define a Data Source

```bash
curl -X POST http://localhost:9002/api/v1/data/sources \
  -H "Content-Type: application/json" \
  -d '{
    "environment_id": "<environment-id-from-step-2>",
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
  }'
```

### Step 4: Create a Data Model

```bash
curl -X POST http://localhost:9002/api/v1/data/models \
  -H "Content-Type: application/json" \
  -d '{
    "environment_id": "<environment-id-from-step-2>",
    "data_source_id": "<data-source-id-from-step-3>",
    "name": "Sales Model",
    "description": "Sales data model"
  }'
```

### Step 5: Create a Semantic Metric

```bash
curl -X POST http://localhost:9002/api/v1/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "monthly_revenue",
    "description": "Total revenue aggregated by month",
    "data_model_id": "<data-model-id-from-step-4>",
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
        "type": "time",
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
  }'
```

### Step 6: Execute the Metric

```bash
curl -X POST http://localhost:9002/api/v1/metrics/<metric-id>/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "start_date": "2024-01-01"
    },
    "cache": {
      "enabled": true,
      "ttl": 3600
    }
  }'
```

## Next Steps

Now that you have Cortex running, explore these topics:

- **[Semantic Layer](../../core/semantics/README.md)** - Learn to create advanced metrics
- **[Query Engine](../../core/query/README.md)** - Understand query execution and caching
- **[Data Sources](../../core/data/sources/README.md)** - Connect to more data sources
- **[Dashboards](../../core/dashboards/README.md)** - Build interactive dashboards
- **[API Reference](../../api/README.md)** - Explore all available endpoints
- **[Multi Tenancy](multi-tenancy.md)** - Set up workspaces and environments
- **[Development](development.md)** - Contribute to Cortex

## Troubleshooting

### Database Connection Issues

**Problem**: Cannot connect to database

**Solutions:**
1. Verify database credentials in `.env`
2. Ensure database is running and accessible
3. Check firewall rules and network connectivity
4. Test connection manually using `psql` or database client

### Migration Issues

**Problem**: Migrations fail to apply

**Solutions:**
1. Check database permissions
2. Review migration logs for specific errors
3. Manually run migrations with `alembic upgrade head`
4. See [Migration Guide](../../migrations/MIGRATION_GUIDE.md) for details

### Port Already in Use

**Problem**: Port 9002 or 9003 already in use

**Solutions:**
```bash
# Use different ports
export CORTEX_API_PORT= 8002
export CORTEX_JOBS_PORT=8003
python -m cortex
```

### Cache Connection Issues

**Problem**: Cannot connect to Redis

**Solutions:**
1. Ensure Redis is running: `redis-cli ping`
2. Use in-memory cache for development: `export CORTEX_CACHE_BACKEND=memory`
3. Check Redis URL configuration

## Support

For additional help:

- [GitHub Issues](https://github.com/TelescopeAI/cortex/issues)
- [Email Support](mailto:help@jointelescope.com)
- [Documentation](https://docs.jointelescope.com)
