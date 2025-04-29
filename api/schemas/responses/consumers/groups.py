from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Json

from api.schemas.responses.consumers.consumers import ConsumerResponse
from cortex.core.types.telescope import TSModel


class ConsumerGroupResponse(TSModel):
    id: UUID
    environment_id: UUID
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Json] = None
    created_at: datetime
    updated_at: datetime


class ConsumerGroupDetailResponse(ConsumerGroupResponse):
    consumers: List[ConsumerResponse] = []


class ConsumerGroupMembershipResponse(TSModel):
    is_member: bool
