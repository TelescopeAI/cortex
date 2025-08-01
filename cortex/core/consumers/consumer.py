from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

import pytz
from pydantic import Field

from cortex.core.types.telescope import TSModel


class Consumer(TSModel):
    id: UUID = -1
    environment_id: UUID
    first_name: str
    last_name: str
    email: str
    organization: Optional[str]
    properties: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now(pytz.UTC)
    updated_at: datetime = datetime.now(pytz.UTC)
