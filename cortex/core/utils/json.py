import base64
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID
from cortex.core.types.telescope import TSModel

def json_default_encoder(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, TSModel):
        # Use mode='json' to ensure UUIDs, datetimes, etc. are properly serialized
        return value.model_dump(mode='json')
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, set):
        return list(value)
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except Exception:
            return base64.b64encode(value).decode("ascii")
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, default=json_default_encoder)

