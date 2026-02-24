# Doctor Module

The doctor module diagnoses misconfigured Cortex entities (metrics, metric variants) and generates concrete fix suggestions. It is designed to grow and support diagnosis for other entities (dashboards, etc.) in the future.

## Architecture

```
cortex/core/doctor/
├── chief.py                          # CortexDoctor — top-level orchestrator
├── surgeons/
│   └── metrics/
│       ├── metric.py                 # MetricSurgeon — diagnoses SemanticMetric
│       ├── variants.py               # VariantSurgeon — diagnoses SemanticMetricVariant
│       └── joins.py                  # JoinInferenceService — auto-detects missing joins
└── README.MD
```

### Types

Defined in `cortex/core/types/doctor.py`:

- **`Suggestion`** — A concrete fix: `description` (why the error occurred) + `fixed` (corrected entity JSON).
- **`Diagnosis`** — `explanation` (all issues, fixable and non-fixable) + `suggestions` (only fixable issues with concrete fixes).
- **`DiagnosisResult`** — `healthy: bool` + optional `diagnosis`.

### Flow

```
API Request
  → CortexDoctor (chief.py)
    → resolves entity by ID or uses inline definition
    → dispatches to the appropriate surgeon
      → MetricSurgeon (5 stages) or VariantSurgeon (compilation + delegation)
    → returns DiagnosisResult
```

## CortexDoctor (chief.py)

Top-level orchestrator with two static methods:

- **`diagnose_metric(metric_id, metric, environment_id)`** — Fetches metric (by ID or inline), resolves DataModel and source type, delegates to `MetricSurgeon`.
- **`diagnose_variant(variant_id, variant, environment_id)`** — Fetches variant (by ID or inline), delegates to `VariantSurgeon`.

Both accept either an entity ID or an inline definition (exactly one must be provided).

## MetricSurgeon (surgeons/metrics/metric.py)

Diagnoses a resolved `SemanticMetric` through 5 sequential stages. All stages run regardless of earlier failures — errors are collected, not short-circuited.

| Stage | Check | Fixable |
|-------|-------|---------|
| 1. Structure | Required fields (`name`, `table_name`/`query`), at least one component | Suggest `table_name` from data source schema |
| 2. Semantics | `ValidationService.validate_metric_execution()` | Fix `data_model_id` mismatch |
| 3. Derivations | `DerivationValidator.validate()` | Closest measure name match, missing `order_dimension`/`partition_by` |
| 4. Joins | `JoinInferenceService.find_missing_join_tables()` | Auto-generate LEFT JOINs from schema metadata |
| 5. Execution | `QueryExecutor.execute_metric(preview=True)` | Non-fixable (query generation / connection errors) |

## VariantSurgeon (surgeons/metrics/variants.py)

Diagnoses a `SemanticMetricVariant` in two phases:

**Phase 1 — Compilation (Stage 0):** Compiles the variant via `compile_metric(variant, fetcher)`, catching compiler-specific errors:

| Error | Fixable |
|-------|---------|
| `CircularReferenceError` | No |
| `MaxDepthExceededError` | No |
| `IncompatibleSourceError` | Yes — fix `environment_id`, `data_model_id`, `data_source_id` to match source metric |
| `InvalidJoinDimensionError` | Yes — suggest closest matching dimension |
| `MeasureNotFoundError` | Yes — suggest closest matching measure |
| `InvalidDerivationError` | Depends on error type |

**Phase 2 — Delegation:** If compilation succeeds, the resolved `SemanticMetric` is passed to `MetricSurgeon.diagnose()` for stages 1-5.

## JoinInferenceService (surgeons/metrics/joins.py)

Ported from the frontend auto-join detection logic. Detects tables referenced in measures/dimensions/filters that have no join to the base table, then infers joins using three strategies (in priority order):

1. **Foreign key relationships** from the database schema metadata
2. **Exact column name matches** between tables (prioritizing `id` columns)
3. **FK naming patterns** (e.g., `id` in one table ↔ `{table}_id` in the other, with singularization)

## API Endpoints

| Method | Path | Request Body | Handler |
|--------|------|-------------|---------|
| POST | `/metrics/diagnose` | `MetricDiagnoseRequest` | `MetricsHandler.diagnose()` |
| POST | `/metrics/variants/diagnose` | `VariantDiagnoseRequest` | `MetricVariantsHandler.diagnose()` |

### Request Schemas (`cortex/sdk/schemas/requests/doctor.py`)

```python
MetricDiagnoseRequest:
    metric_id: Optional[UUID]           # ID of saved metric (mutually exclusive with metric)
    metric: Optional[SemanticMetric]    # Inline metric definition
    environment_id: UUID

VariantDiagnoseRequest:
    variant_id: Optional[UUID]                    # ID of saved variant (mutually exclusive with variant)
    variant: Optional[SemanticMetricVariant]      # Inline variant definition
    environment_id: UUID
```

### Response Schema (`cortex/sdk/schemas/responses/doctor.py`)

```python
DiagnoseResponse:
    healthy: bool
    diagnosis: Optional[Diagnosis]      # null when healthy=True
        explanation: str                # Human-readable summary of ALL issues
        suggestions: List[Suggestion]   # Only fixable issues
            description: str            # Why the error occurred
            fixed: Dict[str, Any]       # Corrected entity JSON
```

### Example Response (unhealthy)

```json
{
  "healthy": false,
  "diagnosis": {
    "explanation": "2 issues found:\n  1. Missing FROM-clause entries for tables: kpi_benchmarks.\n  2. Query execution error: ...",
    "suggestions": [
      {
        "description": "Missing joins detected for tables: kpi_benchmarks. Auto-generated LEFT JOINs: orders.benchmark_id = kpi_benchmarks.id.",
        "fixed": { "...corrected metric JSON with joins added..." }
      }
    ]
  }
}
```

## Adding Support for New Entities

To add doctor support for a new entity type (e.g., dashboards):

1. Create a new surgeon under `cortex/core/doctor/surgeons/<entity>/`.
2. Add a `diagnose_<entity>` method to `CortexDoctor` in `chief.py`.
3. Add the `diagnose()` method to the entity's SDK handler (base/direct/remote).
4. Add a `POST /<entity>/diagnose` endpoint to the entity's API router.
5. Create request schema in `cortex/sdk/schemas/requests/doctor.py`.
