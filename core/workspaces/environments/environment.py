from typing import Optional
from uuid import UUID
from datetime import datetime
import pytz
from pydantic import BaseModel, ConfigDict

from core.types.telescope import TSModel


class WorkspaceEnvironment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = -1
    workspace_id: UUID
    name: str = "Development"
    description: Optional[str] = "Default environment for the workspace environment"
    created_at: datetime = datetime.now(pytz.UTC)
    updated_at: datetime = datetime.now(pytz.UTC)
