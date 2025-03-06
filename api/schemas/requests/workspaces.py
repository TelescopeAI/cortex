from typing import Optional
from pydantic import BaseModel


class WorkspaceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None