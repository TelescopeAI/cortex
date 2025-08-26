# cortex

## Lightweight Modular Analytics Platform

A modular, lightweight analytics engine built in Python to power customer-facing analytics applications. The platform provides a unified semantic layer for defining business data models, a dynamic query engine that integrates with heterogeneous data sources, and a robust user management and authorization system—all accessible via a FastAPI-powered REST API. The semantic layer is designed to support advanced AI agent integration for intelligent analytics, natural language querying, and automated insights generation.

## Overview

This platform is designed to abstract complex data sources into a business-friendly semantic layer. It enables developers to define data models in JSON (with YAML support planned), dynamically generate queries across multiple data sources, and securely expose analytics functionality to both admin/developer users and end users.

### Key Features

- **Semantic Layer**
  - Define and manage data models in JSON with measures, dimensions, and filters
  - Dynamic schema generation with plugin support
  - Advanced output formatting with IN_QUERY and POST_QUERY transformation modes
  - Versioning and audit trails

- **Query Engine**
  - Translates semantic definitions into optimized queries
  - Supports multi-source queries (SQL, NoSQL, files, APIs)
  - Real-time output formatting during query execution and post-processing
  - Integration with caching for enhanced performance [PLANNED]

- **Data Source Integration**
  - Connectors for PostgreSQL, MySQL, BigQuery, Snowflake, MongoDB
  - Support for file-based sources (CSV, Excel, Google Sheets) [PLANNED]

- **API-First Approach**
  - All functionality exposed via FastAPI-based REST endpoints
  - Clear separation of admin and end-user API flows

- **Monitoring & Metrics**
  - Event logging and metrics aggregation to track system health

- **Automated Configuration**
  - Auto-detect and update semantic models based on underlying data source changes

- **Multi-Tenancy & Environment Isolation**
  - Workspace and environment-level isolation to support multiple tenants

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

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL (or other supported database)

### Installation

#### Basic Installation (Core Only)
```bash
# Clone the repository
git clone https://github.com/TelescopeAI/cortex
cd cortex

# Install core dependencies only
poetry install --only main

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the development server (core only)
poetry run python -m cortex.core.main
```

#### Full Installation with API Extras
```bash
# Install with all dependencies including FastAPI
poetry install --with api

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the development server with API
poetry run uvicorn cortex.api.main:app --reload
```

#### Using pip with Extras
```bash
# Install core package
pip install .

# Install with API extras
pip install .[api]
```

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
      "query": "DATE_TRUNC('month', sale_date)",
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

## Frontend

The platform includes a modern Vue.js frontend built with Nuxt.js for creating and managing dashboards, metrics, and data visualizations.

### Frontend Features
- **Metric Builder**: Visual interface for creating semantic metrics with measures, dimensions, and filters
- **Output Format Editor**: Configure data transformations for each semantic object
- **Dashboard Builder**: Drag-and-drop dashboard creation with multiple chart types
- **Advanced Charting**: ECharts integration with support for stacked charts, data zoom, and toolbox features
- **Real-time Preview**: Instant visualization of metric results during development

### Frontend Setup
```bash
cd frontend/cortex
yarn install
yarn dev
```

## Development

### Project Structure
```
cortex/
├── cortex/                   # Core Python package
│   ├── api/                  # FastAPI REST API (optional)
│   ├── core/                 # Core semantic layer and query engine
├── frontend/                 # Nuxt based admin interface
└── pyproject.toml            # Poetry configuration
```

### Key Components
- **Semantic Models**: Core data modeling with measures, dimensions, and filters
- **Query Engine**: SQL generation and execution across multiple data sources
- **Output Processing**: Real-time data transformation and formatting
- **Dashboard Engine**: Widget execution and visualization rendering
- **Frontend Components**: Vue.js components for metric and dashboard management

