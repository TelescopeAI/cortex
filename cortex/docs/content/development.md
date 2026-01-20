# Development Guide

This guide provides information for developers who want to contribute to Cortex or extend its functionality.

## Project Structure

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
│   │   ├── services/         # Business logic services
│   │   ├── storage/          # Database models
│   │   ├── types/            # Type definitions
│   │   ├── utils/            # Utility functions
│   │   └── workspaces/       # Multi-tenancy
│   ├── jobs/                 # Background jobs server
│   │   ├── cache/            # Cache management for file storage
│   │   │   └── manager.py    # LRU cache manager with GCS backing
│   │   ├── tasks/            # Scheduled tasks
│   │   │   └── cache_eviction.py  # Cache eviction task (every 2 hours)
│   │   ├── registry.py       # Plombery pipeline registration
│   │   ├── server.py         # Jobs server launcher
│   │   └── __main__.py       # Direct jobs server entry point
│   ├── migrations/           # Alembic database migrations
│   │   ├── alembic/          # Alembic configuration
│   │   │   ├── versions/     # Migration files
│   │   │   │   ├── sqlite/   # SQLite-specific migrations
│   │   │   │   ├── postgresql/ # PostgreSQL-specific migrations
│   │   │   │   └── mysql/    # MySQL-specific migrations
│   │   │   ├── env.py        # Alembic environment configuration
│   │   │   └── script.py.mako # Migration script template
│   │   ├── alembic.ini       # Alembic configuration file
│   │   └── MIGRATION_GUIDE.md # Database migrations guide
│   ├── app.py                # Unified app launcher (API + Jobs)
│   ├── __main__.py           # Top-level entry point
│   └── __version__.py        # Version information
├── frontend/cortex/          # Nuxt admin interface
│   ├── app/                  # Nuxt application
│   │   ├── components/       # Vue components
│   │   ├── composables/      # Composable functions
│   │   ├── pages/            # Page components
│   │   ├── types/            # TypeScript types
│   │   └── app.vue           # Root application component
│   ├── nuxt.config.ts        # Nuxt configuration
│   └── package.json          # Node dependencies
└── pyproject.toml            # Poetry dependencies
```

## Development Setup

### Backend Development

**Prerequisites:**
- Python 3.12+
- Poetry
- PostgreSQL (or SQLite for local dev)
- Redis (optional, for caching)

**Setup:**

```bash
# Clone the repository
git clone https://github.com/TelescopeAI/cortex
cd cortex

# Install dependencies with Poetry
poetry install --with api --extras gcloud

# Set up environment variables
cp local.env .env
# Edit .env with your configuration

# Run database migrations
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true

# Start API server in development mode
poetry run python -m cortex.api

# Or use the unified launcher
poetry run python -m cortex
```

### Frontend Development (Studio)

**Prerequisites:**
- Node.js 18+
- Yarn or npm

**Setup:**

```bash
cd frontend/cortex

# Install dependencies
yarn install

# Start development server
yarn run dev

# Build for production
yarn run build

# Preview production build
yarn run preview
```

**Studio Features:**

- **Workspace & Environment Management**: Multi-tenant workspace management with environment isolation
- **Data Source Configuration**: Visual interface for connecting and configuring data sources
- **Data Model Builder**: Create and manage data models with schema introspection
- **Metric Builder**: Visual interface for creating semantic metrics
  - Metric preview mode to validate definitions before saving
  - Automated metric recommendations from database schemas
- **Dashboard Builder**: Create multi-view dashboards with drag-and-drop widget placement
  - Embedded metrics: Define metrics directly in dashboard widgets
- **Visualization Editor**: Configure 10+ chart types with advanced field mapping
- **Consumer & Group Management**: Manage end users and consumer groups
- **Query History**: View and analyze query execution history and performance
- **Pre-aggregation Management**: Configure and monitor rollup tables
- **Real-time Preview**: Instant visualization of metric results during development

**Development server:**
- Frontend: `http://localhost:3000`
- Hot module replacement enabled
- Auto-restart on file changes

## Key Components

### Backend Components

#### Semantic Layer

**Location**: `cortex/core/semantics/`

**Responsibilities:**
- Parsing and validating metric definitions
- Managing measures, dimensions, filters
- Output formatting system
- Parameter substitution

**Key Classes:**
- `SemanticMetric` - Metric definition model
- `Measure` - Aggregatable metrics
- `Dimension` - Grouping attributes
- `Filter` - Query filters
- `MetricValidator` - Validation pipeline

[📖 Full Documentation](../../core/semantics/README.md)

#### Query Engine

**Location**: `cortex/core/query/`

**Responsibilities:**
- SQL generation from semantic definitions
- Query execution across data sources
- Result caching
- Query history tracking

**Key Classes:**
- `QueryExecutor` - Main query execution engine
- `QueryBuilder` - SQL generation
- `CacheManager` - Multi-backend caching
- `QueryHistoryService` - Execution logging

[📖 Full Documentation](../../core/query/README.md)

#### Cache Manager

**Location**: `cortex/core/cache/`

**Implementations:**
- `RedisCache` - Distributed caching
- `InMemoryCache` - In Process local caching

**Features:**
- TTL-based expiration
- Cache key generation
- Automatic invalidation

#### Pre-aggregation Service

**Location**: `cortex/core/preaggregations/`

**Responsibilities:**
- Creating and managing rollup tables
- Query rewriting to use pre-aggregations
- Refresh scheduling

#### Dashboard Engine

**Location**: `cortex/core/dashboards/`

**Responsibilities:**
- Dashboard and widget management
- Widget execution coordination
- Field mapping and transformations
- Embedded metric support

[📖 Full Documentation](../../core/dashboards/README.md)

####Consumer Management

**Location**: `cortex/core/consumers/`

**Responsibilities:**
- Consumer and group management
- Property management
- Context-aware query filtering

### Frontend Components

#### Workspace Management

Multi-tenant workspace and environment configuration interface.

#### Data Source Configurator

Visual database connection setup with:
- Connection testing
- Schema introspection
- Configuration validation

#### Metric Builder

Drag-and-drop semantic metric creation with:
- Visual measure/dimension builder
- Filter configuration
- Output formatting
- Parameter definition
- Real-time preview

#### Dashboard Designer

Multi-view dashboard builder with:
- Widget library
- Drag-and-drop layout
- Field mapping editor
- Real-time execution preview

#### Query Explorer

Query history and performance monitoring:
- Execution timeline
- Performance analytics
- Cache hit rates
- Slow query identification

## Contributing Guidelines

### Code Style

**Python:**
- Follow PEP 8 style guide
- Use Black for formatting
- Maximum line length: 100 characters
- Type hints required for public APIs

**TypeScript/Vue:**
- Follow ESLint configuration
- Use Prettier for formatting
- Composition API for Vue components
- TypeScript strict mode enabled

### Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/tooling changes

**Examples:**
```
feat(semantics): add support for window functions in measures

fix(query): resolve cache key collision for parameterized metrics

docs(api): update endpoint documentation for dashboards
```

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feat/my-feature`
3. **Make your changes** with clear commits
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Run tests and linters** to ensure quality
7. **Submit pull request** with description of changes

### Adding New Features

#### Adding a New Data Connector

1. Create connector class in `cortex/core/connectors/`:

```python
from cortex.core.connectors.base import BaseConnector

class MyConnector(BaseConnector):
    def execute_query(self, sql: str):
        # Implementation
        pass
```

2. Register in connector factory
3. Add tests
4. Update documentation

#### Adding a New Visualization Type

1. Add type to dashboard engine
2. Implement frontend component
3. Add field mapping configuration
4. Update documentation

#### Adding a New Output Formatter

1. Create formatter in `cortex/core/semantics/formatters/`
2. Register in formatter registry
3. Add tests
4. Update semantic layer documentation

## Development Workflow

### Local Development

```bash
# Terminal 1: Start API server with auto-reload
poetry run uvicorn cortex.api.main:app --reload --port 9002

# Terminal 2: Start Jobs server
CORTEX_ENABLE_JOBS=true poetry run python -m cortex.jobs

# Terminal 3: Start frontend
cd frontend/cortex && yarn dev

# Terminal 4: Redis (if using cache)
redis-server
```

### Hot Reloading

- **API**: Auto-reloads on Python file changes (with `--reload` flag)
- **Frontend**: Hot module replacement (HMR) enabled by default
- **Jobs**: Requires manual restart

### Debugging

**Python:**

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use debugger in IDE (VSCode, PyCharm)
```

**TypeScript/Vue:**

```typescript
// Use browser DevTools
console.log('Debug info:', data);
debugger;  // Breakpoint
```

## Deployment

### Production Build

**Backend:**

```bash
# Build package
poetry build

# Install in production
pip install dist/telescope-cortex-*.whl

# Start with production settings
EXECUTION_ENV=production python -m cortex
```

**Frontend:**

```bash
cd frontend/cortex

# Build for production
yarn build

# Preview build
yarn preview

# Or deploy to static hosting
# Build outputs to `.output` directory
```

### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY cortex ./cortex

CMD ["python", "-m", "cortex"]
```

### Environment Variables

See [Getting Started](getting-started.md#environment-configuration) for complete environment variable documentation.

## Resources

### Documentation

- [Getting Started](getting-started.md)
- [Architecture](architecture.md)
- [Semantic Layer](../../core/semantics/README.md)
- [Query Engine](../../core/query/README.md)
- [Data Sources](../../core/data/sources/README.md)
- [Dashboards](../../core/dashboards/README.md)
- [API Reference](../../api/README.md)
- [Multi Tenancy](multi-tenancy.md)

### External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Nuxt 4 Documentation](https://nuxt.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Vue 3 Documentation](https://vuejs.org/)

## License

This project is licensed under the MIT License - see the [LICENSE](../../../LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/TelescopeAI/cortex/issues)
- [Pull Requests](https://github.com/TelescopeAI/cortex/compare)
- [Email](mailto:help@jointelescope.com)
