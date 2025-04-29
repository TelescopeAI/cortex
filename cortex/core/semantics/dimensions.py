from typing import Optional

from cortex.core.types.telescope import TSModel


class SemanticDimension(TSModel):
    name: str
    description: Optional[str] = None
    primary_key: Optional[str] = None
