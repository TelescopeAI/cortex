# Cortex Studio

A modern, comprehensive analytics platform frontend built with Nuxt 4. Studio provides an intuitive interface for creating and managing dashboards, metrics, data sources, and multi-tenant workspaces.

## Overview

Cortex Studio is the frontend interface for the Telescope Cortex analytics platform. It provides a complete visual environment for:

- **Workspace & Environment Management**: Multi-tenant workspace management with environment isolation
- **Data Source Configuration**: Visual interface for connecting and configuring various data sources
- **Data Model Builder**: Create and manage data models with schema introspection
- **Metric Builder**: Visual interface for creating semantic metrics with measures, dimensions, filters, and aggregations
- **Dashboard Builder**: Create multi-view dashboards with drag-and-drop widget placement
- **Visualization Editor**: Configure 10+ chart types with advanced field mapping
- **Consumer & Group Management**: Manage end users and consumer groups
- **Query History**: View and analyze query execution history and performance
- **Pre-aggregation Management**: Configure and monitor rollup tables

## Technology Stack

- **Framework**: Nuxt 4
- **Language**: TypeScript with full type safety
- **UI Library**: Shadcn/ui components with Tailwind CSS
- **Charts**: Apache ECharts with nuxt-echarts integration
- **State Management**: Vue 3 Composables with reactive state
- **Form Validation**: VeeValidate with Zod schemas
- **Drag & Drop**: FormKit drag-and-drop for dashboard widgets
- **Code Highlighting**: Shiki for SQL and code syntax highlighting
- **Package Manager**: Yarn

## Features

### 🏢 Multi-Tenant Workspace Management
- Create and manage workspaces for different organizations
- Environment isolation (dev, staging, production)
- Hierarchical organization structure

### 📊 Advanced Dashboard Builder
- Multi-view dashboard system (executive, operational, tactical)
- Drag-and-drop widget placement
- 10+ visualization types: single value, gauge, bar/line/area/pie/donut charts, scatter plots, heatmaps, and tables
- Real-time widget execution and preview
- Widget-level metric execution with override support

### 🔧 Visual Metric Builder
- Intuitive interface for creating semantic metrics
- Support for measures, dimensions, filters, and aggregations
- Advanced output formatting with IN_QUERY and POST_QUERY modes
- Parameter system for dynamic query generation
- Metric extension and inheritance support

### 🗄️ Data Source Integration
- Visual configuration for multiple database types
- Support for PostgreSQL, MySQL, BigQuery, SQLite, MongoDB
- Schema introspection and humanized schema generation
- Connection testing and validation

### 👥 User Management
- Consumer and consumer group management
- Role-based access control
- Environment-level user isolation

### 📈 Analytics & Monitoring
- Query execution history and performance analytics
- Cache hit rate tracking and statistics
- Pre-aggregation management and monitoring
- Real-time query execution logs

## Project Structure

```
frontend/cortex/
├── app/
│   ├── components/           # Vue components
│   │   ├── charts/          # Chart components (ECharts)
│   │   ├── dashboards/      # Dashboard-related components
│   │   ├── data-sources/    # Data source configuration components
│   │   ├── metric/builder/  # Metric builder components
│   │   └── ui/              # Shadcn/ui components
│   ├── composables/         # Vue 3 composables for state management
│   ├── pages/               # Nuxt pages (routes)
│   │   ├── dashboards/      # Dashboard management pages
│   │   ├── metrics/         # Metric management pages
│   │   ├── data/            # Data source and model pages
│   │   ├── consumers/       # User management pages
│   │   └── workspaces/      # Workspace management pages
│   ├── types/               # TypeScript type definitions
│   └── assets/              # Static assets and styles
├── components.json          # Shadcn/ui configuration
├── nuxt.config.ts          # Nuxt configuration
├── package.json            # Dependencies and scripts
└── tailwind.config.ts      # Tailwind CSS configuration
```

## Setup

### Prerequisites
- Node.js 22+ 
- Yarn package manager
- Telescope Cortex backend running on `http://localhost:9002`

### Installation

```bash
# Install dependencies
yarn install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration

Key environment variables:
```bash
# API Configuration
API_BASE_URL=http://localhost:9002

# Development settings
NUXT_DEVTOOLS_ENABLED=true
```

## Development

### Start Development Server

```bash
# Start the development server on http://localhost:3000
yarn dev
```

### Build for Production

```bash
# Build the application
yarn build

# Generate static files
yarn run generate
```

## Key Components

### Dashboard System
- **DashboardContainer**: Main dashboard layout and widget management
- **DashboardSection**: Section-based widget organization
- **ViewWidget**: Individual widget display and interaction
- **ChartRenderer**: ECharts integration for visualizations

### Metric Builder
- **MetricSchemaBuilder**: Visual metric definition interface
- **MeasuresBuilder**: Measure configuration
- **DimensionsBuilder**: Dimension configuration
- **FiltersBuilder**: Filter configuration
- **OutputFormatEditor**: Advanced formatting options

### Data Management
- **DataSourceConfig**: Database connection configuration
- **DataModelBuilder**: Data model creation and management
- **SchemaViewer**: Database schema visualization

### User Interface
- **Shadcn/ui Components**: Modern, accessible UI components
- **Theme System**: Dark/light mode support
- **Responsive Design**: Mobile-friendly interface
- **Toast Notifications**: User feedback system

## API Integration

Studio communicates with the Telescope Cortex backend via REST API:

- **Workspaces**: `/api/v1/workspaces`
- **Environments**: `/api/v1/environments`
- **Data Sources**: `/api/v1/data/sources`
- **Data Models**: `/api/v1/data/models`
- **Metrics**: `/api/v1/metrics`
- **Dashboards**: `/api/v1/dashboards`
- **Consumers**: `/api/v1/consumers`
- **Query History**: `/api/v1/query/history`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Support

For questions and support:
- Open an issue on GitHub
- Email: info@jointelescope.com
- Documentation: [Cortex Docs](https://docs.jointelescope.com)
