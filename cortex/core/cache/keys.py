import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cortex.core.semantics.refresh_keys import RefreshKey, RefreshKeyType


def _canonicalize(obj: Dict[str, Any]) -> str:
    """Return a canonical JSON string for a dict: sorted keys, no spaces, drop None values."""
    filtered = {k: v for k, v in obj.items() if v is not None}
    return json.dumps(filtered, sort_keys=True, separators=(",", ":"))


def build_query_signature(payload: Dict[str, Any]) -> str:
    """Build an MD5 32-hex signature from a canonicalized JSON payload."""
    canonical = _canonicalize(payload)
    return hashlib.md5(canonical.encode("utf-8")).hexdigest()


def derive_time_bucket(now: datetime, refresh_key: Optional[RefreshKey]) -> Optional[str]:
    """Derive a coarse time bucket label based on RefreshKey.

    For type 'every', we floor to the nearest period boundary. For other types, return None.
    """
    if not refresh_key:
        return None
    if refresh_key.type == RefreshKeyType.EVERY and refresh_key.every:
        # naive parser for formats like "1 hour", "30 minutes", "1 day"
        try:
            parts = refresh_key.every.strip().split()
            if len(parts) != 2:
                return None
            amount = int(parts[0])
            unit = parts[1].lower()
            if unit.startswith("hour"):
                floored = now.replace(minute=0, second=0, microsecond=0)
                step = timedelta(hours=amount)
            elif unit.startswith("minute"):
                floored = now.replace(second=0, microsecond=0)
                step = timedelta(minutes=amount)
            elif unit.startswith("day"):
                floored = now.replace(hour=0, minute=0, second=0, microsecond=0)
                step = timedelta(days=amount)
            else:
                return None
            # compute bucket start aligned to step
            delta = now - floored
            steps = int(delta.total_seconds() // step.total_seconds())
            bucket_start = floored + steps * step
            # format label
            if unit.startswith("hour"):
                return f"hour:{bucket_start.strftime('%Y-%m-%dT%H')}"
            if unit.startswith("minute"):
                return f"minute:{bucket_start.strftime('%Y-%m-%dT%H:%M')}"
            if unit.startswith("day"):
                return f"day:{bucket_start.strftime('%Y-%m-%d')}"
            return None
        except Exception:
            return None
    return None


def build_cache_key(signature: str) -> str:
    """Build the final cache key string from a signature."""
    return f"cortex:v1:{signature}"