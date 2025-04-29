from typing import List, Optional
from uuid import UUID

from cortex.core.types.telescope import TSModel


class SemanticConsumerContext(TSModel):
    allowed_groups: Optional[List[UUID]] = None
    filters: Optional[str] = None
