import json
from datetime import datetime
from typing import Optional
from pydantic import Json, field_validator

from core.types.ts_model import TSModel


class EnvironmentProperty(TSModel):
    id: int = -1
    key_name: str
    key_value: str
    meta: Optional[Json]
    comments: Optional[str]
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    @field_validator("meta")
    @classmethod
    def validate_json(cls, v):
        if isinstance(v, dict):
            v = json.dumps(v, default=str, sort_keys=True)
        return v

    class Config:
        orm_mode = True
