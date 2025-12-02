from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

import pytz
from pydantic import Field, ConfigDict

from cortex.core.types.telescope import TSModel


class DataModel(TSModel):
    """
    Data model that represents a collection of metrics with shared configuration.
    Supports versioning and serves as a logical grouping for related metrics.
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    environment_id: UUID
    name: str
    alias: Optional[str] = None
    description: Optional[str] = None
    
    # Versioning support
    version: int = 1
    is_active: bool = True
    parent_version_id: Optional[UUID] = None  # For version branching
    
    # Custom configuration dictionary for model-level settings
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation state
    is_valid: bool = False
    validation_errors: Optional[List[str]] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(pytz.UTC))
