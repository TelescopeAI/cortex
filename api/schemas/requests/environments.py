from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class EnvironmentCreateRequest(BaseModel):
    workspace_id: UUID
    name: str = "Development"
    description: Optional[str] = "Default environment for the workspace environment"


class EnvironmentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None