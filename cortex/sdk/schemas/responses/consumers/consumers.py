from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import EmailStr

from cortex.core.types.telescope import TSModel


class ConsumerResponse(TSModel):
    id: UUID
    environment_id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    organization: Optional[str]
    properties: Optional[Dict[str, Any]] = None
    groups: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime
