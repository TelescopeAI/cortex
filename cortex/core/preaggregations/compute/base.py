from typing import Optional, Protocol

from cortex.core.preaggregations.models import (
    EngineCapabilities,
    EngineType,
    PreAggregationBuildOptions,
    PreAggregationSpec,
)


class ComputeAdapter(Protocol):
    def engine(self) -> EngineType: ...

    def capabilities(self) -> EngineCapabilities: ...

    def build_or_refresh(self, spec: PreAggregationSpec, build_options: Optional[PreAggregationBuildOptions] = None) -> None: ...


