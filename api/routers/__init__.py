from typing import List


from api.docs.main import DocsRouter
from api.routers.consumers.consumers import ConsumersRouter
from api.routers.consumers.groups import ConsumerGroupsRouter
from api.routers.data.sources import DataSourcesRouter
from api.routers.environments import EnvironmentsRouter
from api.routers.workspaces import WorkspaceRouter

ROUTES: List[dict] = [
    {"router": DocsRouter, "enabled": True, "internal": False},
    {"router": WorkspaceRouter, "enabled": True, "internal": False},
    {"router": EnvironmentsRouter, "enabled": True, "internal": False},
    {"router": ConsumersRouter, "enabled": True, "internal": False},
    {"router": DataSourcesRouter, "enabled": True, "internal": False},
    {"router": ConsumerGroupsRouter, "enabled": True, "internal": False},
]

ENABLED_ROUTES = list(filter(lambda route: route["enabled"] is True, ROUTES))
PUBLIC_ROUTES = list(filter(lambda route: route["internal"] is False, ENABLED_ROUTES))
