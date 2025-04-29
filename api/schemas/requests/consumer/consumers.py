from typing import Optional
from uuid import UUID
from pydantic import EmailStr

from cortex.core.types.telescope import TSModel


class ConsumerCreateRequest(TSModel):
    environment_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str] = None


class ConsumerUpdateRequest(TSModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    organization: Optional[str] = None