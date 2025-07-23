from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

import pytz
from pydantic import Field

from cortex.core.types.telescope import TSModel


class ModelVersion(TSModel):
    """
    Represents a historical version of a DataModel for audit trails and version management.
    Stores complete snapshots of semantic models at specific points in time.
    """
    id: UUID = Field(default_factory=uuid4)
    data_model_id: UUID  # Reference to the parent DataModel
    version_number: int
    
    # Complete semantic model snapshot
    semantic_model: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation state at time of version creation
    is_valid: bool = False
    validation_errors: Optional[List[str]] = None
    compiled_queries: Optional[Dict[str, str]] = None  # metric_alias -> query
    
    # Version metadata
    description: Optional[str] = None  # Description of changes in this version
    created_by: Optional[UUID] = None  # User who created this version
    tags: Optional[List[str]] = None   # Tags for categorizing versions
    
    # Legacy config (for backward compatibility)
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        } 