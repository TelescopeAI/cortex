# Cortex Core

The Core package contains the fundamental components that power the Cortex analytics engine. This modular architecture enables flexible data modeling, efficient query execution, and powerful visualization capabilities.

![Core Architecture](../docs/assets/core_architecture_diagram.png)
## Core Modules

### Semantic Layer
The semantic layer provides a business-friendly abstraction over raw data sources. It enables you to define metrics, dimensions, and measures in JSON format, creating a unified data model that can be queried consistently across different data sources. The semantic layer supports advanced features like output formatting, parameter systems, and AI agent integration for intelligent analytics.

📖 [Read the Semantic Layer documentation](semantics/README.md)

### Query Engine
The query engine translates semantic definitions into optimized SQL queries and executes them across heterogeneous data sources. It features multi-layer caching (Redis and in-memory), pre-aggregations for performance optimization, and comprehensive query history tracking. The engine supports real-time output formatting and post-processing transformations.

📖 [Read the Query Engine documentation](query/README.md)

### Data Sources
The data sources module provides connectors for various database systems and file formats. It supports PostgreSQL, MySQL, BigQuery, SQLite, and spreadsheet data sources (CSV, Google Sheets). The module includes schema introspection capabilities, connection management, and an extensible factory pattern for adding custom connectors.

📖 [Read the Data Sources documentation](data/sources/README.md)

### Dashboards
The dashboard system enables creation of multi-view analytics dashboards with support for 10+ visualization types including charts, gauges, tables, and heatmaps. It features embedded metrics (define metrics directly in widgets), real-time preview, field mapping, and data transformations. Dashboard types include executive, operational, and tactical views.

📖 [Read the Dashboard documentation](dashboards/README.md)

## Quick Links

- [API Reference](../api/README.md) - REST API endpoints and usage
- [Getting Started](../docs/content/getting-started.md) - Installation and setup guide
- [Architecture Overview](../docs/content/architecture.md) - High-level system architecture
- [Multi Tenancy](../docs/content/multi-tenancy.md) - Workspaces and environment isolation
- [Development Guide](../docs/content/development.md) - Contributing and development workflow

## Key Features

- **Modular Design**: Each component can be used independently or as part of the complete system
- **Type Safety**: Comprehensive Pydantic models for validation and serialization
- **Extensibility**: Plugin-based architecture for custom connectors and formatters
- **Performance**: Multi-layer caching and pre-aggregation support
- **AI-Ready**: Designed for integration with AI agents and natural language interfaces
