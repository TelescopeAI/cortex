from cortex.core.preaggregations.models import PreAggregationSpec
from cortex.core.preaggregations.scheduler.base import SchedulerAdapter


class AutocronScheduler(SchedulerAdapter):
    def schedule_refresh(self, spec: PreAggregationSpec) -> None:
        # MVP stub: no-op
        return None

    def trigger_refresh_now(self, spec_id: str) -> None:
        # MVP stub: no-op
        return None

    def cancel(self, spec_id: str) -> None:
        # MVP stub: no-op
        return None


