# Semantic Layer

The Cortex Semantic Layer provides a business-friendly abstraction over raw data sources, enabling you to define metrics, dimensions, and measures in JSON format. This creates a unified, reusable data model that can be queried consistently across different data sources.

![Semantic Layer Architecture](../../docs/assets/semantic_layer_architecture.png)
## Overview

The semantic layer is the foundation of Cortex's analytics capabilities. It allows you to:

- Define business metrics once and reuse them everywhere
- Abstract complex SQL logic into simple, named metrics
- Ensure consistent metric definitions across your organization
- Enable non-technical users to query data using business terminology
- Support AI agent integration for natural language analytics

## Creating Semantic Models

Semantic models are defined in JSON format and consist of several key components:

### Basic Structure

```json
{
  "name": "customer_revenue",
  "description": "Customer revenue metrics with monthly aggregation",
  "table_name": "transactions",
  "data_model_id": "uuid-of-data-model",
  "measures": [...],
  "dimensions": [...],
  "filters": [...],
  "parameters": [...]
}
```

### Measures

Measures are quantitative metrics that can be aggregated. They support various aggregation types:

```json
{
  "name": "total_revenue",
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
```

**Supported aggregation types:**
- `sum` - Sum of values
- `avg` - Average value
- `count` - Count of records
- `count_distinct` - Count of unique values
- `min` / `max` - Minimum/maximum values

### Dimensions

Dimensions are categorical attributes used for grouping and filtering:

```json
{
  "name": "customer_segment",
  "query": "segment",
  "type": "string"
}
```

**Time dimensions** with formatting:

```json
{
  "name": "month",
  "query": "transaction_date",
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
```

### Filters

Filters restrict the data returned by a metric:

```json
{
  "name": "active_customers_only",
  "query": "status = 'active'"
}
```

### Conditional Logic

Cortex supports conditional logic for dynamic column combinations:

```json
{
  "name": "revenue_by_channel",
  "type": "sum",
  "query": "CASE WHEN channel = 'web' THEN web_amount WHEN channel = 'mobile' THEN mobile_amount ELSE 0 END"
}
```

## Output Formatting

The semantic layer supports two modes of output formatting:

### In-Query Formatting (`in_query`)

Applied during SQL generation, before query execution:

```json
{
  "name": "date_cast",
  "type": "cast",
  "mode": "in_query",
  "target_type": "date"
}
```

### Post-Query Formatting (`post_query`)

Applied to results after query execution:

```json
{
  "name": "currency_format",
  "type": "format",
  "mode": "post_query",
  "format_string": "${:,.2f}"
}
```

**Available formatters:**
- `format` - Python format string
- `cast` - Type conversion
- `round` - Numeric rounding
- `date_format` - Date/time formatting

## Parameter System

Parameters enable dynamic query generation with runtime values:

```json
{
  "name": "date_range_metric",
  "measures": [{
    "name": "revenue",
    "type": "sum",
    "query": "amount"
  }],
  "filters": [{
    "name": "date_filter",
    "query": "transaction_date >= {{start_date}} AND transaction_date <= {{end_date}}"
  }],
  "parameters": [
    {
      "name": "start_date",
      "type": "date",
      "required": true
    },
    {
      "name": "end_date",
      "type": "date",
      "required": true
    }
  ]
}
```

**Execute with parameters:**

```python
from cortex.core.query.executor import QueryExecutor

result = executor.execute_metric(
    metric=metric,
    data_model=data_model,
    parameters={
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
)
```

## Versioning & Audit Trails

All semantic metrics support versioning and audit trails:

- **Version Control**: Track changes to metric definitions over time
- **Audit Logs**: Record who created/modified metrics and when
- **Rollback**: Restore previous versions of metrics if needed

## Metric Discovery

Cortex provides automated metric discovery from database schemas:

- **Schema Introspection**: Automatically detect tables and columns
- **Metric Recommendations**: Suggest metrics based on column types and names
- **Preview Mode**: Validate metric definitions before saving

![Metric Definition Flow](../../docs/assets/metric_definition_example.png)
*Example of metric definition with visual flow*

## AI Agent Integration Points

The semantic layer is designed for AI agent integration:

1. **Natural Language Interface**: AI agents can translate user questions into `SemanticMetric` instances
2. **Intelligent Discovery**: Semantic search across available metrics and dimensions
3. **Automated Modeling**: AI-powered generation of data models from schema analysis
4. **Context Personalization**: Leverage consumer properties for role-based metric suggestions
5. **Pattern Learning**: AI agents can learn from query patterns and execution history

## Validation Pipeline

All semantic models go through a validation pipeline:

1. **Schema Validation**: Ensure all referenced tables/columns exist
2. **Type Checking**: Validate measure and dimension types
3. **Parameter Validation**: Check required parameters are provided
4. **SQL Compilation**: Verify generated SQL is valid
5. **Execution Test**: Optional dry-run to validate query execution

## Example: Complete Semantic Metric

```json
{
  "name": "monthly_revenue_by_segment",
  "description": "Monthly revenue broken down by customer segment",
  "table_name": "transactions",
  "data_model_id": "abc-123",
  "measures": [
    {
      "name": "revenue",
      "type": "sum",
      "query": "amount",
      "formatting": [
        {
          "name": "currency",
          "type": "format",
          "mode": "post_query",
          "format_string": "${:,.2f}"
        }
      ]
    },
    {
      "name": "transaction_count",
      "type": "count",
      "query": "id"
    }
  ],
  "dimensions": [
    {
      "name": "month",
      "query": "DATE_TRUNC('month', transaction_date)",
      "type": "time"
    },
    {
      "name": "customer_segment",
      "query": "segment",
      "type": "string"
    }
  ],
  "filters": [
    {
      "name": "completed_only",
      "query": "status = 'completed'"
    }
  ],
  "parameters": [
    {
      "name": "min_amount",
      "type": "number",
      "required": false,
      "default": 0
    }
  ]
}
```

## Best Practices

1. **Use Descriptive Names**: Make metric names self-explanatory
2. **Document Everything**: Add descriptions to all metrics and dimensions
3. **Leverage Parameters**: Use parameters for dynamic, reusable metrics
4. **Format Appropriately**: Apply formatting to improve readability
5. **Test Before Saving**: Use preview mode to validate metrics
6. **Version Control**: Track important metrics in version control
7. **Organize by Domain**: Group related metrics in the same data model

## Related Documentation

- [Query Engine](../query/README.md) - How queries are generated and executed
- [Data Sources](../data/sources/README.md) - Connecting to data sources
- [API Reference](../../api/README.md) - REST API for metric management
- [Multi Tenancy](../../docs/content/multi-tenancy.md) - Context-aware query execution
