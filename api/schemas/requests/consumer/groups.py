from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Json


class ConsumerGroupCreateRequest(BaseModel):
    environment_id: UUID
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Json] = None


class ConsumerGroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Json] = None


class ConsumerGroupMembershipRequest(BaseModel):
    consumer_id: UUID
