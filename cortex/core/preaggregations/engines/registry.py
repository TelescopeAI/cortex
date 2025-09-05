from typing import Dict

from cortex.core.preaggregations.models import EngineType, EngineCapabilities
from cortex.core.preaggregations.engines.capabilities import POSTGRES_CAPABILITIES


class EngineRegistry:
    def __init__(self) -> None:
        self._caps: Dict[EngineType, EngineCapabilities] = {
            EngineType.POSTGRES: POSTGRES_CAPABILITIES,
        }

    def get_capabilities(self, engine: EngineType) -> EngineCapabilities:
        if engine not in self._caps:
            raise ValueError(f"Unsupported engine: {engine}")
        return self._caps[engine]


