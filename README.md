# cortex

## AI-Enhanced Modular Analytics Platform

A modular, lightweight analytics engine built in Python to power customer-facing analytics applications. The platform provides a unified semantic layer for defining business data models, a dynamic query engine that integrates with heterogeneous data sources, and a robust user management and authorization system—all accessible via a FastAPI-powered REST API. The semantic layer is designed to support advanced AI agent integration for intelligent analytics, natural language querying, and automated insights generation.

## Overview

This platform is designed to abstract complex data sources into a business-friendly semantic layer. It enables developers to define data models in JSON (with YAML support planned), dynamically generate queries across multiple data sources, and securely expose analytics functionality to both admin/developer users and end users.

### Key Features

- **Semantic Layer**
  - Define and manage data models in JSON
  - Dynamic schema generation with plugin support
  - Versioning and audit trails (integrated with Git)

- **Query Engine**
  - Translates semantic definitions into optimized queries
  - Supports multi-source queries (SQL, NoSQL, files, APIs)
  - Integration with caching for enhanced performance

- **Data Source Integration**
  - Connectors for PostgreSQL, MySQL, BigQuery, Snowflake, MongoDB
  - Support for file-based sources (CSV, Excel, Google Sheets)

- **User Management & Authentication**
  - Admin/dev authentication using FastAPI and fastapi-users
  - End user authentication via JWT, mapped to local user records

- **Authorization**
  - Out-of-the-box RBAC with extensible hooks for dynamic, rule-based (ABAC-like) policies
  - Plugin interface for custom authorization logic

- **API-First Approach**
  - All functionality exposed via FastAPI-based REST endpoints
  - Clear separation of admin and end-user API flows

- **Caching & Performance**
  - Redis integration for caching query results and configuration data

- **Monitoring & Metrics**
  - Event logging and metrics aggregation to track system health

- **Automated Configuration**
  - Auto-detect and update semantic models based on underlying data source changes

- **Multi-Tenancy & Environment Isolation**
  - Workspace and environment-level isolation to support multiple tenants

- **AI Agent Integration Ready**
  - Semantic layer optimized for AI agent integration
  - Natural language query processing capabilities
  - Context-aware personalization and recommendations
  - Automated metric discovery and data model generation
  - Intelligent query optimization and performance tuning

## Architecture

The project follows a layered architecture within a monorepo, ensuring modularity, ease of maintenance, and independent evolution of key components.

### Semantic Layer for AI Integration

The semantic layer is designed with AI agent integration in mind, providing:

- **Structured Semantic Models**: JSON-based metric definitions with measures, dimensions, joins, and aggregations
- **Context-Aware Execution**: Consumer properties and environment isolation for personalized data access
- **Query Abstraction**: Database-agnostic query generation from semantic definitions
- **Execution Logging**: Comprehensive query execution logs for AI training and optimization
- **Parameter System**: Dynamic parameter substitution for flexible query generation
- **Validation Pipeline**: Automated validation and compilation of semantic models

This foundation enables AI agents to:
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
- Python 3.9+
- PostgreSQL (or other supported database)
- Redis (for caching)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd cortex

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the development server
poetry run uvicorn cortex.api.main:app --reload
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

2. **Create a Semantic Metric**:
```json
{
  "name": "monthly_revenue",
  "description": "Total revenue aggregated by month",
  "table_name": "sales",
  "measures": [
    {
      "name": "revenue",
      "type": "sum",
      "query": "amount"
    }
  ],
  "dimensions": [
    {
      "name": "month",
      "query": "DATE_TRUNC('month', sale_date)"
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

## Roadmap

### Phase 1: AI Foundation
- [ ] Natural language query interface
- [ ] Semantic metric discovery and search
- [ ] Basic recommendation engine
- [ ] Enhanced query logging for AI training

### Phase 2: Intelligent Analytics
- [ ] Automated data model generation from schema analysis
- [ ] AI-powered query optimization
- [ ] Context-aware personalization
- [ ] Anomaly detection and data quality monitoring

### Phase 3: Advanced AI Capabilities
- [ ] Multi-agent orchestration system
- [ ] Semantic knowledge graph
- [ ] Predictive analytics and forecasting
- [ ] Collaborative intelligence features

### Phase 4: Enterprise AI
- [ ] Domain-specific AI models
- [ ] Advanced governance and compliance
- [ ] Real-time insights generation
- [ ] Federated learning across tenants

