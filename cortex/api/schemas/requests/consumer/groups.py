from typing import Optional, Dict, Any
from uuid import UUID

from cortex.core.types.telescope import TSModel

class ConsumerGroupCreateRequest(TSModel):
    environment_id: UUID
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class ConsumerGroupUpdateRequest(TSModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class ConsumerGroupMembershipRequest(TSModel):
    consumer_id: UUID
