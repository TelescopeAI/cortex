from typing import Dict, Optional
from uuid import UUID

from pydantic import Field

from cortex.core.types.telescope import TSModel
from cortex.core.types.time import TimeGrain
from cortex.core.query.engine.bindings.base import QuerySourceBinding


class RollupBindingModel(TSModel):
    qualified_table: str
    dimension_columns: Dict[str, str] = Field(default_factory=dict)
    measure_columns: Dict[str, str] = Field(default_factory=dict)
    time_bucket_columns: Dict[str, str] = Field(default_factory=dict)
    rollup_grain: Optional[TimeGrain] = None
    pre_aggregation_spec_id: Optional[UUID] = None

    def to_query_binding(self) -> QuerySourceBinding:
        mapping = {**self.dimension_columns, **self.measure_columns, **self.time_bucket_columns}
        return _RollupBindingAdapter(
            qualified_table=self.qualified_table,
            column_mapping=mapping,
            rollup_grain=self.rollup_grain,
            pre_aggregation_spec_id=self.pre_aggregation_spec_id,
        )


class _RollupBindingAdapter(TSModel):
    qualified_table: str
    column_mapping: Dict[str, str]
    rollup_grain: Optional[TimeGrain] = None
    spec_id: Optional[UUID] = None

    # Adapt to Protocol attribute name expected by QuerySourceBinding
    @property
    def pre_aggregation_spec_id(self) -> Optional[str]:
        return str(self.spec_id) if self.spec_id else None


