from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
import pytz
from pydantic import Field, Json

from cortex.core.types.telescope import TSModel


class ConsumerGroup(TSModel):
    id: UUID = Field(default_factory=uuid4)
    environment_id: UUID
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    properties: Optional[Json] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
