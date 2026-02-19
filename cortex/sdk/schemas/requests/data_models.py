from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import Field
from cortex.core.types.telescope import TSModel


class DataModelCreateRequest(TSModel):
    """Request schema for creating a new data model."""
    environment_id: UUID = Field(..., description="Environment ID for the data model")
    name: str = Field(..., description="Name of the data model")
    alias: Optional[str] = Field(None, description="Alias for the data model")
    description: Optional[str] = Field(None, description="Description of the data model")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Model configuration")


class DataModelUpdateRequest(TSModel):
    """Request schema for updating an existing data model."""
    environment_id: UUID = Field(..., description="Environment ID for the data model")
    name: Optional[str] = Field(None, description="Name of the data model")
    alias: Optional[str] = Field(None, description="Alias for the data model")
    description: Optional[str] = Field(None, description="Description of the data model")
    config: Optional[Dict[str, Any]] = Field(None, description="Model configuration")
    is_active: Optional[bool] = Field(None, description="Whether the model is active")


class ModelExecutionRequest(TSModel):
    """Request schema for executing a metric from a data model."""
    metric_alias: str = Field(..., description="Alias of the metric to execute")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Runtime parameters for the metric")


class ModelValidationRequest(TSModel):
    """Request schema for validating a data model."""
    validate_dependencies: bool = Field(True, description="Whether to validate metric dependencies")
    validate_syntax: bool = Field(True, description="Whether to validate syntax")


class ModelVersionCreateRequest(TSModel):
    """Request schema for creating a new version of a data model."""
    description: Optional[str] = Field(None, description="Description of changes in this version")
    tags: Optional[list[str]] = Field(None, description="Tags for this version")


class ModelRestoreRequest(TSModel):
    """Request schema for restoring a data model to a specific version."""
    version_id: UUID = Field(..., description="ID of the version to restore to")
    create_backup: bool = Field(True, description="Whether to create a backup before restoring") 