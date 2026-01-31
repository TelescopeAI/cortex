# Cortex Use Cases

This guide explores practical use cases for Cortex from two perspectives: personal projects and SaaS/product development.

## Personal Use Cases

### 1. Personal Finance Dashboard

Connect your bank export (CSV) or Google Sheets budget tracker as a data source, then build metrics like:

```json
{
  "name": "monthly_spending_by_category",
  "measures": [{"name": "total", "type": "sum", "query": "amount"}],
  "dimensions": [{"name": "category", "type": "string", "query": "category"}],
  "filters": [{"query": "type = 'expense'"}]
}
```

**What you can build:**
- Track spending trends with line charts
- Category breakdown with pie/donut charts
- Single-value KPIs for savings rate
- Budget vs. actual with gauges

### 2. Side Project Analytics

Self-hosted alternative to Amplitude/Mixpanel:

- Connect your PostgreSQL/SQLite database directly
- Define user engagement metrics (DAU, retention, conversion)
- Build executive dashboards with gauges and trends
- Query history to identify slow queries in your app

### 3. Investment Portfolio Tracker

- Import stock data via CSV/Sheets
- Build metrics for portfolio allocation, P&L by sector
- Heatmaps for correlation analysis
- Real-time refresh for live data

### 4. Fitness/Health Data Hub

- Export data from various apps to Sheets
- Unified metrics across sleep, workouts, nutrition
- Trend analysis with area charts
- Goal tracking with gauges

### 5. Content Creator Analytics

- Aggregate YouTube, Twitter, Substack data in Sheets
- Cross-platform metrics (engagement rate, growth)
- Audience breakdown by platform
- Revenue tracking with currency formatting

---

## SaaS Founder / Product Manager Use Cases

### 1. Embedded Analytics for Your Product (Revenue Driver)

**The Play**: Add analytics as a premium feature tier

```
Your SaaS Product
    │
    ├── API calls to Cortex
    │   POST /api/v1/metrics/{id}/execute
    │
    └── Display results in your UI (React/Vue/etc)
```

**Multi-Tenant Setup:**

```
Workspace: Your SaaS (internal)
├── Environment: Customer A (Production)
│   ├── Consumer: customer_a_user_1 {plan: "pro", company_id: "A"}
│   └── Consumer: customer_a_user_2 {plan: "pro", company_id: "A"}
├── Environment: Customer B (Production)
│   └── Consumer: customer_b_user_1 {plan: "enterprise", company_id: "B"}
```

Row-level security via consumer properties ensures users only see their data automatically.

### 2. Product Analytics Backend

Replace expensive tools (Amplitude at $50k+/year) with self-hosted Cortex:

| Cortex Feature | Replaces |
|----------------|----------|
| Semantic metrics | Amplitude computed properties |
| Consumer properties | Cohort definitions |
| Query history | Event explorer |
| Dashboards | Custom dashboards |
| Pre-aggregations | Materialized views |

**Cost Savings**: Run on a $50/mo server vs. $5k+/mo for analytics SaaS

### 3. Customer-Facing Reporting Portal

Build a white-labeled reporting product:

```python
# Embed dashboard in customer portal
dashboard_result = httpx.post(
    f"{CORTEX_URL}/api/v1/dashboards/{dashboard_id}/execute",
    headers={"X-Consumer-ID": current_user.consumer_id}  # Row-level security
)
# Render widgets using your frontend framework
```

**Monetization**: Charge $X/seat for "Advanced Analytics" tier

### 4. Internal Business Intelligence

For your startup's own metrics:

| Dashboard Type | Metrics |
|----------------|---------|
| **Executive** | MRR, Churn, LTV, CAC (single values + gauges) |
| **Sales** | Pipeline by stage, conversion rates (bar + funnel) |
| **Product** | Feature adoption, user engagement (line + heatmap) |
| **Support** | Ticket volume, response time (area + table) |

**10+ Visualization Types**: Single value, gauge, bar, line, area, pie, donut, scatter, heatmap, table

### 5. Data Product / API Business

Monetize your data as a service:

```bash
# Your customers call your API
GET /api/metrics/industry-benchmarks?sector=fintech&metric=churn_rate

# You internally route to Cortex
POST /api/v1/metrics/{benchmark_metric_id}/execute
```

**Features you get for free:**
- Caching (Redis) - don't recompute expensive queries
- Pre-aggregations - sub-second response times
- Rate limiting (planned) - usage-based billing ready

### 6. Operational Monitoring Dashboard

Real-time ops for your platform:

```json
{
  "widget": {
    "refresh_config": {
      "enabled": true,
      "interval_seconds": 30
    }
  }
}
```

- API error rates
- Queue depths
- Infrastructure utilization
- Alerting thresholds (with gauges)

---

## Key Differentiators for SaaS Founders

| Feature | Why It Matters |
|---------|----------------|
| **Multi-Tenancy Built-In** | Workspace → Environment → Consumer hierarchy handles customer isolation |
| **Consumer Properties** | Row-level security without writing auth logic |
| **Embedded Metrics** | Rapid prototyping without cluttering metric library |
| **Pre-aggregations** | Enterprise-grade performance at startup costs |
| **Spreadsheet Sources** | Onboard customers who only have Excel/Sheets data |
| **Self-Hosted** | SOC2/HIPAA compliance, data sovereignty |
| **REST API First** | Integrate with any stack (React, Vue, mobile, etc.) |

---

## ROI Calculations

### Scenario A: Replace Metabase + Custom Code

- Metabase hosting: $500/mo
- Developer time for multi-tenant logic: 80 hrs × $150 = $12,000
- **Cortex**: Free (self-hosted) + 8 hrs setup

### Scenario B: Add Analytics to Your SaaS

- Build custom: 3-6 months dev time
- Buy (Cube Cloud + frontend): $2k-10k/mo
- **Cortex**: 1-2 weeks integration, $50/mo hosting

### Scenario C: Customer-Facing Reports as Upsell

- 100 customers × $50/mo analytics add-on = $5k MRR
- Infrastructure cost: ~$200/mo
- **Gross margin: 96%**

---

## Related Documentation

- [Getting Started](getting-started.md) - Installation and setup
- [Multi Tenancy](multi-tenancy.md) - Workspace and environment configuration
- [Dashboards](../../core/dashboards/README.md) - Building visualizations
- [Semantic Layer](../../core/semantics/README.md) - Defining metrics
- [API Reference](../../api/README.md) - Integration endpoints
