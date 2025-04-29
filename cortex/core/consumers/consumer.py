from typing import Optional
from uuid import UUID
from datetime import datetime

import pytz

from cortex.core.types.telescope import TSModel


class Consumer(TSModel):
    id: UUID = -1
    environment_id: UUID
    first_name: str
    last_name: str
    email: str
    organization: Optional[str]
    created_at: datetime = datetime.now(pytz.UTC)
    updated_at: datetime = datetime.now(pytz.UTC)
