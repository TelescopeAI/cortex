from datetime import datetime
from typing import Optional
from uuid import UUID
import pytz
from pydantic import ConfigDict

from cortex.core.types.telescope import TSModel


class Workspace(TSModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID = -1
    name: str
    description: Optional[str]
    created_at: datetime = datetime.now(pytz.UTC)
    updated_at: datetime = datetime.now(pytz.UTC)
