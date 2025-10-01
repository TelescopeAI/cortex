from cortex.core.preaggregations.models import EngineCapabilities, EngineType, TimeGrain


POSTGRES_CAPABILITIES = EngineCapabilities(
    engine=EngineType.POSTGRES,
    supports_materialized_views=True,
    supports_ctas=True,
    supports_indexes=True,
    supports_partitioned_tables=True,
    supported_time_grains=[
        TimeGrain.HOUR,
        TimeGrain.DAY,
        TimeGrain.WEEK,
        TimeGrain.MONTH,
        TimeGrain.QUARTER,
        TimeGrain.YEAR,
    ],
)


