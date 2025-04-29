# cortex/cortex/core/data/modelling/model.py
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

import pytz
from pydantic import Field

from cortex.core.types.telescope import TSModel

class DataModel(TSModel):
    id: UUID = Field(default_factory=uuid4)
    data_source_id: UUID
    name: str
    alias: Optional[str]
    description: Optional[str]
    model_type: str  # e.g., 'cube', 'metrics', 'dimensions'
    config: Dict[str, Any]  # Stores the model configuration in JSON format
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))