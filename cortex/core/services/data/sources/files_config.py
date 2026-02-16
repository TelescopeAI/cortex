"""
File storage configuration with pluggable path generators and lifecycle hooks.

This module provides a centralized way to configure file storage behavior for Cortex,
especially useful when Cortex is used as a library in other codebases.
"""

import contextvars
import logging
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from uuid import UUID

from pydantic import ConfigDict, Field

from cortex.core.types.telescope import TSModel
from cortex.core.connectors.api.sheets.config import get_sheets_config

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models for Path Generators and Hooks
# ============================================================================


class UploadPathGeneratorConfig(TSModel):
    """Configuration passed to upload path generators"""
    workspace_id: UUID
    environment_id: UUID
    filename: str  # Without extension
    extension: str
    source_id: Optional[str] = None
    base_storage_path: str  # From get_sheets_config()
    file_size: Optional[int] = None  # Optional metadata
    mime_type: Optional[str] = None


class SqlitePathGeneratorConfig(TSModel):
    """Configuration passed to SQLite path generators"""
    workspace_id: UUID
    environment_id: UUID
    source_id: str
    base_storage_path: str  # From get_sheets_config()


class HookInvokerConfig(TSModel):
    """Configuration passed to lifecycle hooks"""
    workspace_id: UUID
    environment_id: UUID
    filename: str  # Display name with extension
    event_type: str  # "upload_start", "upload_success", etc.
    file_id: Optional[UUID] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    error: Optional[Exception] = None
    meta: Optional[Dict[str, Any]] = None  # Optional metadata for custom hooks
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


class FileStorageConfig(TSModel):
    """
    Configuration for file storage with pluggable path generators and lifecycle hooks.

    All fields are optional. If not provided, default behavior is used.
    """

    # Path generators - take config objects
    upload_path_generator: Optional[Callable[[UploadPathGeneratorConfig], str]] = None
    sqlite_path_generator: Optional[Callable[[SqlitePathGeneratorConfig], str]] = None

    # Lifecycle hooks - take config objects
    on_upload_start: Optional[Callable[[HookInvokerConfig], None]] = None
    on_upload_success: Optional[Callable[[HookInvokerConfig], None]] = None
    on_upload_error: Optional[Callable[[HookInvokerConfig], None]] = None
    on_delete_start: Optional[Callable[[HookInvokerConfig], None]] = None
    on_delete_success: Optional[Callable[[HookInvokerConfig], None]] = None
    on_delete_error: Optional[Callable[[HookInvokerConfig], None]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


_file_storage_config: contextvars.ContextVar[Optional[FileStorageConfig]] = (
    contextvars.ContextVar("file_storage_config", default=None)
)


def get_file_storage_config() -> FileStorageConfig:
    """
    Get the current file storage config from context, or return default.

    Thread-safe and async-safe using contextvars.
    """
    config = _file_storage_config.get()
    if config is None:
        config = FileStorageConfig()
        _file_storage_config.set(config)
    return config


def set_file_storage_config(config: FileStorageConfig) -> None:
    """
    Set custom file storage config in context (typically called by external codebases).
    """
    _file_storage_config.set(config)
    logger.info("Custom file storage config registered in context")


def default_upload_path_generator(config: UploadPathGeneratorConfig) -> str:
    """
    Default upload path generator.

    IMPORTANT: When source_id is provided, it should ALWAYS be a system-generated UUID (file_id),
    NOT user input. This prevents path injection vulnerabilities and ensures consistent naming.

    File naming pattern:
    - With source_id: workspace_id/environment_id/{source_id}.{extension}
    - Without source_id: workspace_id/environment_id/{filename}.{extension}

    Original filename is preserved in database metadata for display purposes.
    """
    base_path = Path(config.base_storage_path)

    if config.source_id:
        # Use source_id as the filename (not as a subdirectory)
        # This creates: workspace/env/file_id.csv
        return str(base_path / str(config.workspace_id) / str(config.environment_id) / f"{config.source_id}.{config.extension}")

    return str(base_path / str(config.workspace_id) / str(config.environment_id) / f"{config.filename}.{config.extension}")


def default_sqlite_path_generator(config: SqlitePathGeneratorConfig) -> str:
    """Default SQLite path generator"""
    base_path = Path(config.base_storage_path)
    return str(base_path / str(config.workspace_id) / str(config.environment_id) / f"{config.source_id}.db")


def invoke_hook_safely(hook: Optional[Callable[[HookInvokerConfig], None]], config: HookInvokerConfig) -> None:
    """Safely invoke a lifecycle hook"""
    if hook is None:
        return
    
    try:
        hook(config)
    except Exception as exc:
        logger.warning("File storage hook error", exc_info=True, extra={"event_type": config.event_type})
