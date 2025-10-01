from typing import Protocol

from cortex.core.preaggregations.models import PreAggregationSpec


class SchedulerAdapter(Protocol):
    def schedule_refresh(self, spec: PreAggregationSpec) -> None: ...

    def trigger_refresh_now(self, spec_id: str) -> None: ...

    def cancel(self, spec_id: str) -> None: ...


