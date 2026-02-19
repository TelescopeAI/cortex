from datetime import datetime
from typing import Optional
from uuid import UUID

from cortex.core.types.telescope import TSModel


class EnvironmentResponse(TSModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
