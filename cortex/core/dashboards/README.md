# Dashboards & Visualization

The Cortex Dashboard system enables creation of multi-view analytics dashboards with support for 10+ visualization types, embedded metrics, and real-time data execution.

![Dashboard Builder](../../docs/assets/dashboard_builder_interface.png)
*Dashboard builder interface showing widget configuration*

## Overview

Cortex dashboards provide a flexible, powerful way to visualize your data:

- **Multi-View Dashboards**: Executive, operational, and tactical dashboard types
- **10+ Visualization Types**: Charts, gauges, tables, and more
- **Embedded Metrics**: Define metrics directly within widgets
- **Real-time Preview**: Instant visualization during development
- **Field Mapping**: Transform and map data to visualization requirements
- **Widget-Level Overrides**: Customize metric execution per widget

## Dashboard Types

### Executive Dashboards

High-level KPIs and trends for leadership:
- Single value metrics
- Trend indicators
- Comparison charts
- Goal tracking

### Operational Dashboards

Real-time operational metrics:
- Live data feeds
- Alert indicators
- Detailed breakdowns
- Time-series charts

### Tactical Dashboards

Detailed analysis for specific teams:
- Complex visualizations
- Drill-down capabilities
- Comparative analysis
- Custom filters

## Visualization Types

Cortex supports 10+ visualization types powered by ECharts:

### Single Value

Display a single metric value with optional comparison.

```json
{
  "type": "single_value",
  "config": {
    "show_trend": true,
    "comparison_period": "previous_period",
    "format": "currency"
  }
}
```

**Best for:**
- KPIs
- Summary metrics
- Goal tracking

### Gauge

Circular or semi-circular gauge for progress tracking.

```json
{
  "type": "gauge",
  "config": {
    "min": 0,
    "max": 100,
    "target": 80,
    "show_percentage": true
  }
}
```

**Best for:**
- Progress toward goals
- Capacity utilization
- Performance scores

### Bar Chart

Horizontal or vertical bar charts for comparisons.

```json
{
  "type": "bar",
  "config": {
    "orientation": "vertical",
    "stacked": false,
    "show_values": true
  }
}
```

**Best for:**
- Category comparisons
- Ranking data
- Distribution analysis

### Line Chart

Time-series and trend visualization.

```json
{
  "type": "line",
  "config": {
    "smooth": true,
    "show_area": false,
    "show_points": true
  }
}
```

**Best for:**
- Trends over time
- Multiple metrics comparison
- Forecasting

### Area Chart

Filled line charts for magnitude visualization.

```json
{
  "type": "area",
  "config": {
    "stacked": true,
    "smooth": false,
    "opacity": 0.7
  }
}
```

**Best for:**
- Volume over time
- Stacked categories
- Cumulative totals

### Pie Chart

Circular chart for part-to-whole relationships.

```json
{
  "type": "pie",
  "config": {
    "show_labels": true,
    "show_percentages": true,
    "donut": false
  }
}
```

**Best for:**
- Market share
- Category distribution
- Budget allocation

### Donut Chart

Pie chart with center cutout.

```json
{
  "type": "donut",
  "config": {
    "inner_radius": "50%",
    "show_total": true
  }
}
```

**Best for:**
- Similar to pie charts
- Multiple series
- Summary in center

### Scatter Plot

Point-based visualization for correlation analysis.

```json
{
  "type": "scatter",
  "config": {
    "show_regression": true,
    "point_size": 8
  }
}
```

**Best for:**
- Correlation analysis
- Outlier detection
- Pattern recognition

### Heatmap

Matrix visualization for intensity comparison.

```json
{
  "type": "heatmap",
  "config": {
    "color_scheme": "blue_to_red",
    "show_values": true
  }
}
```

**Best for:**
- Time-based patterns
- Cross-tabulation
- Density maps

### Table

Tabular data display with sorting and formatting.

```json
{
  "type": "table",
  "config": {
    "sortable": true,
    "paginated": true,
    "page_size": 20,
    "show_totals": true
  }
}
```

**Best for:**
- Detailed data
- Exportable reports
- Multi-column comparisons

![Visualization Types](../../docs/assets/visualization_types_gallery.png)
*Gallery of available visualization types*

## Creating Dashboards

### Basic Dashboard Structure

```json
{
  "name": "Sales Performance",
  "description": "Monthly sales metrics and trends",
  "dashboard_type": "operational",
  "environment_id": "env-123",
  "layout": {
    "columns": 12,
    "rows": 6
  },
  "widgets": [...]
}
```

### Widget Configuration

Each widget defines:
- Position and size
- Visualization type
- Data source (metric or embedded metric)
- Field mappings
- Display options

```json
{
  "id": "widget-1",
  "name": "Monthly Revenue",
  "type": "line",
  "position": {
    "x": 0,
    "y": 0,
    "width": 6,
    "height": 3
  },
  "metric_id": "monthly_revenue_metric",
  "field_mappings": {
    "x_axis": "month",
    "y_axis": "revenue"
  },
  "config": {
    "smooth": true,
    "show_area": true
  }
}
```

## Embedded Metrics

Define metrics directly within dashboard widgets without saving them separately:

```json
{
  "widget": {
    "name": "Active Users",
    "type": "single_value",
    "embedded_metric": {
      "name": "active_users_today",
      "table_name": "users",
      "measures": [
        {
          "name": "count",
          "type": "count_distinct",
          "query": "user_id"
        }
      ],
      "filters": [
        {
          "name": "active_filter",
          "query": "last_active_at >= CURRENT_DATE"
        }
      ]
    }
  }
}
```

**Benefits:**
- Rapid prototyping
- Widget-specific calculations
- No cluttering metric library
- Easy experimentation

## Field Mapping & Transformations

Map metric outputs to visualization requirements:

### Basic Field Mapping

```json
{
  "field_mappings": {
    "x_axis": "date",
    "y_axis": "revenue",
    "series": "product_category"
  }
}
```

### Advanced Transformations

```json
{
  "field_mappings": {
    "x_axis": {
      "source_field": "month",
      "transform": "date_format",
      "format": "%B %Y"
    },
    "y_axis": {
      "source_field": "revenue",
      "transform": "currency",
      "currency": "USD"
    }
  }
}
```

**Available transformations:**
- `date_format` - Format dates
- `currency` - Format currency
- `percentage` - Convert to percentage
- `number_format` - Number formatting
- `truncate` - Truncate strings
- `uppercase/lowercase` - Text case

## Widget-Level Metric Execution

Override metric execution parameters at the widget level:

```json
{
  "widget": {
    "metric_id": "revenue_metric",
    "execution_overrides": {
      "parameters": {
        "date_range": "last_30_days"
      },
      "filters": [
        {
          "name": "region_filter",
          "query": "region = 'US'"
        }
      ],
      "cache": {
        "enabled": true,
        "ttl": 1800
      }
    }
  }
}
```

## Dashboard Preview

Preview dashboards with real-time metric execution before saving:

```python
from cortex.core.dashboards.service import DashboardService

service = DashboardService()

# Preview dashboard with sample data
preview = service.preview_dashboard(
    dashboard_config=dashboard_json,
    environment_id="env-123"
)

# Returns:
# {
#   "widgets": [
#     {
#       "widget_id": "widget-1",
#       "data": [...],
#       "execution_time_ms": 145
#     }
#   ],
#   "total_execution_time_ms": 423
# }
```

## Real-Time Data Updates

Configure widgets for real-time data updates:

```json
{
  "widget": {
    "refresh_config": {
      "enabled": true,
      "interval_seconds": 30,
      "on_data_change_only": true
    }
  }
}
```

## Dashboard Templates

Use templates for common dashboard patterns:

```python
# Create dashboard from template
dashboard = service.create_from_template(
    template_name="executive_overview",
    environment_id="env-123",
    parameters={
        "date_range": "last_90_days",
        "comparison_period": "previous_quarter"
    }
)
```

**Available templates:**
- `executive_overview` - High-level KPIs
- `sales_performance` - Sales metrics
- `user_engagement` - User analytics
- `financial_summary` - Financial metrics

## Sharing & Permissions

Control dashboard access and sharing:

```json
{
  "dashboard": {
    "sharing": {
      "public": false,
      "shared_with": ["user-123", "group-456"],
      "embed_enabled": true,
      "embed_token": "abc123"
    }
  }
}
```

## Exporting Dashboards

Export dashboards in various formats:

```python
# Export as PDF
service.export_dashboard(
    dashboard_id="dash-123",
    format="pdf",
    output_path="/path/to/dashboard.pdf"
)

# Export as PNG
service.export_dashboard(
    dashboard_id="dash-123",
    format="png",
    output_path="/path/to/dashboard.png"
)

# Export data as CSV
service.export_dashboard_data(
    dashboard_id="dash-123",
    format="csv",
    output_path="/path/to/data.csv"
)
```

## Best Practices

### Dashboard Design

1. **Keep It Simple**: Limit to 6-8 widgets per dashboard
2. **Logical Grouping**: Group related metrics together
3. **Consistent Layout**: Use grid-based layouts
4. **Color Scheme**: Use consistent, meaningful colors
5. **White Space**: Don't overcrowd the dashboard

### Performance

1. **Use Caching**: Enable caching for frequently viewed dashboards
2. **Optimize Metrics**: Ensure underlying metrics are optimized
3. **Lazy Loading**: Load widgets as they come into view
4. **Pre-aggregations**: Use rollups for complex calculations

### User Experience

1. **Clear Titles**: Use descriptive widget titles
2. **Tooltips**: Add helpful tooltips to metrics
3. **Filters**: Provide global filters for interactivity
4. **Drill-Down**: Enable drill-down for detailed analysis
5. **Mobile Friendly**: Ensure dashboards work on mobile devices

## API Usage

### Create Dashboard

```python
import httpx

response = httpx.post("http://localhost:9002/api/v1/dashboards", json={
    "name": "Sales Dashboard",
    "description": "Monthly sales performance",
    "dashboard_type": "operational",
    "environment_id": "env-123",
    "widgets": [...]
})

dashboard = response.json()
```

### Execute Dashboard

```python
# Execute all widgets in a dashboard
response = httpx.post(
    f"http://localhost:9002/api/v1/dashboards/{dashboard_id}/execute"
)

results = response.json()
```

### Update Widget

```python
response = httpx.put(
    f"http://localhost:9002/api/v1/dashboards/{dashboard_id}/widgets/{widget_id}",
    json={
        "name": "Updated Widget",
        "config": {...}
    }
)
```

## Related Documentation

- [Semantic Layer](../semantics/README.md) - Defining metrics for dashboards
- [Query Engine](../query/README.md) - How widget data is executed
- [API Reference](../../api/README.md) - Dashboard management endpoints
- [Frontend Studio](../../docs/content/development.md#studio) - Dashboard builder UI
