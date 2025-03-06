from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import EmailStr

from core.types.telescope import TSModel


class ConsumerResponse(TSModel):
    id: UUID
    environment_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str]
    created_at: datetime
    updated_at: datetime
