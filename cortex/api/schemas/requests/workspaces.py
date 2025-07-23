from typing import Optional
from cortex.core.types.telescope import TSModel


class WorkspaceCreateRequest(TSModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdateRequest(TSModel):
    name: Optional[str] = None
    description: Optional[str] = None