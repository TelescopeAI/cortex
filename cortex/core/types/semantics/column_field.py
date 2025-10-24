from typing import Optional, List, Any, TYPE_CHECKING
from cortex.core.types.telescope import TSModel

if TYPE_CHECKING:
    from cortex.core.semantics.transforms import Transform


class ColumnField(TSModel):
    """
    Reference to a database column with optional transforms.
    Reusable across measures, dimensions, filters, and conditions.
    
    Example:
        ColumnField(column="status", table="users")
        ColumnField(
            column="amount",
            transforms=[Transform(function="ROUND", params={"decimals": 2})]
        )
    """
    column: str
    table: Optional[str] = None
    
    # Optional: For when the field itself needs transforms before use
    transforms: Optional[List[Any]] = None  # List['Transform'] but avoid circular import
