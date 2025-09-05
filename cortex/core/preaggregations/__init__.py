# Cortex Pre-aggregations package
import os

from cortex.core.preaggregations.models import PreAggregationEnvConfig, SchedulerKind, TimeGrain, \
    PreAggregationStorageMode
from cortex.core.preaggregations.service import PreAggregationService


def load_env_config() -> PreAggregationEnvConfig:
    enabled = str(os.getenv("CORTEX_PREAGGREGATIONS_ENABLED", "false")).lower() == "true"
    scheduler_kind = os.getenv("CORTEX_PREAGGREGATIONS_SCHEDULER", SchedulerKind.AUTOCRON.value)
    rq_redis_url = os.getenv("CORTEX_PREAGGREGATIONS_RQ_REDIS_URL")
    rq_queue = os.getenv("CORTEX_PREAGGREGATIONS_RQ_QUEUE", "default")
    celery_broker = os.getenv("CORTEX_PREAGGREGATIONS_CELERY_BROKER_URL")
    celery_backend = os.getenv("CORTEX_PREAGGREGATIONS_CELERY_BACKEND_URL")
    celery_queue = os.getenv("CORTEX_PREAGGREGATIONS_CELERY_QUEUE", "default")
    huey_url = os.getenv("CORTEX_PREAGGREGATIONS_HUEY_URL")
    default_grain = os.getenv("CORTEX_PREAGGREGATIONS_DEFAULT_GRAIN", TimeGrain.DAY.value)
    default_storage = os.getenv("CORTEX_PREAGGREGATIONS_DEFAULT_STORAGE", PreAggregationStorageMode.SOURCE.value)

    try:
        kind = SchedulerKind(scheduler_kind)
    except Exception:
        kind = SchedulerKind.AUTOCRON

    try:
        grain = TimeGrain(default_grain)
    except Exception:
        grain = TimeGrain.DAY

    try:
        storage_mode = PreAggregationStorageMode(default_storage)
    except Exception:
        storage_mode = PreAggregationStorageMode.SOURCE

    return PreAggregationEnvConfig(
        enabled=enabled,
        scheduler_kind=kind,
        rq_redis_url=rq_redis_url,
        rq_queue=rq_queue,
        celery_broker_url=celery_broker,
        celery_backend_url=celery_backend,
        celery_queue=celery_queue,
        huey_url=huey_url,
        default_grain=grain,
        default_storage_mode=storage_mode,
    )


_GLOBAL_SERVICE = PreAggregationService()


def get_service() -> PreAggregationService:
    return _GLOBAL_SERVICE
