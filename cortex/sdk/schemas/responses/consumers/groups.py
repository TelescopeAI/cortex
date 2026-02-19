from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from cortex.api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.core.types.telescope import TSModel


class ConsumerGroupResponse(TSModel):
    id: UUID
    environment_id: UUID
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ConsumerGroupDetailResponse(ConsumerGroupResponse):
    consumers: List[ConsumerResponse] = []


class ConsumerGroupMembershipResponse(TSModel):
    is_member: bool
