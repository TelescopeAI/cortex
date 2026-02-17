from typing import List


from cortex.api.docs.main import DocsRouter
from cortex.api.routers.admin.cache import AdminCacheRouter
from cortex.api.routers.consumers.consumers import ConsumersRouter
from cortex.api.routers.consumers.groups import ConsumerGroupsRouter
from cortex.api.routers.data.models import DataModelsRouter
from cortex.api.routers.data.sources import DataSourcesRouter
from cortex.api.routers.environments import EnvironmentsRouter
from cortex.api.routers.preaggregations import PreAggregationsRouter
from cortex.api.routers.workspaces import WorkspaceRouter
from cortex.api.routers.metrics import MetricsRouter
from cortex.api.routers.variants import VariantsRouter
from cortex.api.routers.dashboards.dashboards import DashboardRouter
from cortex.api.routers.query_history import QueryHistoryRouter

ROUTES: List[dict] = [
    {"router": DocsRouter, "enabled": True, "internal": False},
    {"router": WorkspaceRouter, "enabled": True, "internal": False},
    {"router": EnvironmentsRouter, "enabled": True, "internal": False},
    {"router": ConsumersRouter, "enabled": True, "internal": False},
    {"router": DataSourcesRouter, "enabled": True, "internal": False},
    {"router": ConsumerGroupsRouter, "enabled": True, "internal": False},
    {"router": DataModelsRouter, "enabled": True, "internal": False},
    {"router": VariantsRouter, "enabled": True, "internal": False},  # Must come before MetricsRouter (more specific routes first)
    {"router": MetricsRouter, "enabled": True, "internal": False},
    {"router": DashboardRouter, "enabled": True, "internal": False},
    {"router": QueryHistoryRouter, "enabled": True, "internal": False},
    {"router": PreAggregationsRouter, "enabled": True, "internal": False},
    {"router": AdminCacheRouter, "enabled": True, "internal": True},  # Admin endpoints, hidden from public API
]

ENABLED_ROUTES = list(filter(lambda route: route["enabled"] is True, ROUTES))
PUBLIC_ROUTES = list(filter(lambda route: route["internal"] is False, ENABLED_ROUTES))
# All enabled routes (includes internal ones like admin)
ALL_ENABLED_ROUTES = ENABLED_ROUTES
