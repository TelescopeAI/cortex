from datetime import datetime
from typing import Optional
from uuid import UUID

from cortex.core.types.telescope import TSModel


class WorkspaceResponse(TSModel):
    id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
