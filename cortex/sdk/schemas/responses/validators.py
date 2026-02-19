from typing import Optional

from cortex.core.types.telescope import TSModel


class DBValidationResult(TSModel):
    can_connect: bool = False
    non_null_tables: bool = False
    error: Optional[str] = None
