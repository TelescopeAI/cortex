from typing import Optional
from uuid import UUID

from cortex.core.types.telescope import TSModel


class EnvironmentCreateRequest(TSModel):
    workspace_id: UUID
    name: str = "Development"
    description: Optional[str] = "Default environment for the workspace environment"


class EnvironmentUpdateRequest(TSModel):
    name: Optional[str] = None
    description: Optional[str] = None