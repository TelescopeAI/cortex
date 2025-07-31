from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import EmailStr, Json

from cortex.core.types.telescope import TSModel


class ConsumerResponse(TSModel):
    id: UUID
    environment_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str]
    properties: Optional[Json] = None
    groups: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime
