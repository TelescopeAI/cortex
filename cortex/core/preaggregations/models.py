from enum import Enum
from typing import List, Optional, Tuple, Union, Dict
from datetime import datetime
from uuid import UUID

from cortex.core.types.telescope import TSModel
from cortex.core.types.time import TimeGrain
from cortex.core.semantics.metrics.metric import SemanticMetric
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.refresh_keys import RefreshPolicy
from pydantic import Field


class FilterOperator(str, Enum):
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    LIKE = "like"


Scalar = Union[str, int, float, bool, None]
ScalarArray = List[Scalar]
ScalarRange = Tuple[Scalar, Scalar]


class EngineType(str, Enum):
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"
    SNOWFLAKE = "snowflake"
    REDSHIFT = "redshift"
    CLICKHOUSE = "clickhouse"
    TRINO = "trino"
    DUCKDB = "duckdb"
    DATABRICKS = "databricks"
    MSSQL = "mssql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DataSourceRef(TSModel):
    data_source_id: str
    engine: EngineType
    schema: Optional[str] = None
    table: str


class PreAggregationFilter(TSModel):
    column: str
    op: FilterOperator
    value: Union[Scalar, ScalarArray, ScalarRange]


class PreAggregationStorageMode(str, Enum):
    SOURCE = "source"
    REMOTE = "remote"


class PreAggregationStorageConfig(TSModel):
    mode: PreAggregationStorageMode
    engine: Optional[EngineType] = None
    path: Optional[str] = None
    resolver_id: Optional[str] = None
    resolver_options: Optional[Dict[str, str]] = None


class PreAggregationPartitionConfig(TSModel):
    by: str
    grain: TimeGrain


class PreAggregationBuildStrategy(str, Enum):
    MATERIALIZED_VIEW = "materialized_view"
    CTAS = "ctas"
    SWAP = "swap"


class PreAggregationBuildConfig(TSModel):
    strategy: PreAggregationBuildStrategy = Field(default=PreAggregationBuildStrategy.MATERIALIZED_VIEW)
    atomic: bool = Field(default=False)
    select_sql: Optional[str] = None


class PreAggregationType(str, Enum):
    ROLLUP = "rollup"
    ORIGINAL_SQL = "original_sql"
    ROLLUP_LAMBDA = "rollup_lambda"


class PreAggregationSpec(TSModel):
    id: str
    type: PreAggregationType
    metric_id: UUID
    name: Optional[str] = None
    source: DataSourceRef
    dimensions: List[SemanticDimension]
    measures: List[SemanticMeasure]
    filters: Optional[List[PreAggregationFilter]] = None
    refresh: Optional[RefreshPolicy] = None
    storage: PreAggregationStorageConfig
    partitions: Optional[PreAggregationPartitionConfig] = None
    build: Optional[PreAggregationBuildConfig] = None


class PreAggregationPlanResult(TSModel):
    covered: bool
    spec_id: Optional[str] = None
    reason: Optional[str] = None
    projected_select: Optional[str] = None
    rollup_binding: Optional["RollupBindingModel"] = None


class PreAggregationBuildOptions(TSModel):
    force_full_rebuild: bool = Field(default=True)


class EngineCapabilities(TSModel):
    engine: EngineType
    supports_materialized_views: bool
    supports_ctas: bool
    supports_indexes: bool
    supports_partitioned_tables: bool
    supported_time_grains: List[TimeGrain]
    supports_external_stage: bool = Field(default=False)
    supports_federated_query: bool = Field(default=False)


class SchedulerKind(str, Enum):
    AUTOCRON = "autocron"
    RQ = "rq"
    CELERY = "celery"
    HUEY = "huey"


class AutocronSchedulerConfig(TSModel):
    kind: SchedulerKind = Field(default=SchedulerKind.AUTOCRON)
    interval: str = Field(default="1 hour")


class RQSchedulerConfig(TSModel):
    kind: SchedulerKind = Field(default=SchedulerKind.RQ)
    redis_url: str
    queue: str = Field(default="default")


class CelerySchedulerConfig(TSModel):
    kind: SchedulerKind = Field(default=SchedulerKind.CELERY)
    broker_url: str
    backend_url: Optional[str] = None
    queue: str = Field(default="default")


class HueySchedulerConfig(TSModel):
    kind: SchedulerKind = Field(default=SchedulerKind.HUEY)
    url: str


PreAggregationScheduler = Union[
    AutocronSchedulerConfig,
    RQSchedulerConfig,
    CelerySchedulerConfig,
    HueySchedulerConfig,
]


class PreAggregationSchedulerMap(TSModel):
    default: PreAggregationScheduler
    overrides: Dict[str, PreAggregationScheduler] = Field(default_factory=dict)


class PreAggregationConfig(TSModel):
    enabled: bool = Field(default=False)
    scheduler: Optional[PreAggregationScheduler] = None


class PreAggregationEnvConfig(TSModel):
    enabled: bool = Field(default=False)
    scheduler_kind: SchedulerKind = Field(default=SchedulerKind.AUTOCRON)
    rq_redis_url: Optional[str] = None
    rq_queue: str = Field(default="default")
    celery_broker_url: Optional[str] = None
    celery_backend_url: Optional[str] = None
    celery_queue: str = Field(default="default")
    huey_url: Optional[str] = None
    default_grain: TimeGrain = Field(default=TimeGrain.DAY)
    default_storage_mode: PreAggregationStorageMode = Field(default=PreAggregationStorageMode.SOURCE)
    default_engine: Optional[EngineType] = None


class PreAggregationStatus(TSModel):
    spec_id: str
    last_refreshed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    row_count: Optional[int] = None
    bytes_written: Optional[int] = None
    error: Optional[str] = None
    dry_run: bool = Field(default=False)
    staleness_seconds: Optional[int] = None


# Import at the end to avoid circular imports, then rebuild models with forward references
try:
    from cortex.core.query.engine.bindings.rollup_binding import RollupBindingModel
    PreAggregationPlanResult.model_rebuild()
except ImportError:
    # If RollupBindingModel is not available, skip the rebuild
    pass


