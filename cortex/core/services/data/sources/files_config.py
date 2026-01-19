"""
File storage configuration with pluggable path generators and lifecycle hooks.

This module provides a centralized way to configure file storage behavior for Cortex,
especially useful when Cortex is used as a library in other codebases.
"""

import contextvars
import logging
from pathlib import Path
from typing import Optional, Callable, Any
from uuid import UUID

from pydantic import ConfigDict

from cortex.core.types.telescope import TSModel
from cortex.core.connectors.api.sheets.config import get_sheets_config

logger = logging.getLogger(__name__)


class FileStorageConfig(TSModel):
    """
    Configuration for file storage with pluggable path generators and lifecycle hooks.

    All fields are optional. If not provided, default behavior is used.
    """

    # Path generators
    upload_path_generator: Optional[Callable[[UUID, str, str, Optional[str]], str]] = None
    sqlite_path_generator: Optional[Callable[[UUID, str], str]] = None

    # Lifecycle hooks
    on_upload_start: Optional[Callable[..., None]] = None
    on_upload_success: Optional[Callable[..., None]] = None
    on_upload_error: Optional[Callable[..., None]] = None
    on_delete_start: Optional[Callable[..., None]] = None
    on_delete_success: Optional[Callable[..., None]] = None
    on_delete_error: Optional[Callable[..., None]] = None

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


def default_upload_path_generator(
    environment_id: UUID,
    filename: str,
    extension: str,
    source_id: Optional[str] = None,
) -> str:
    """
    Default upload path generator that preserves current Cortex behavior.
    """
    config = get_sheets_config()
    base_path = Path(config.input_storage_path)

    if source_id:
        return str(base_path / source_id / f"{filename}.{extension}")

    return str(base_path / f"{filename}.{extension}")


def default_sqlite_path_generator(
    environment_id: UUID,
    source_id: str,
) -> str:
    """
    Default SQLite path generator that preserves current Cortex behavior.
    """
    config = get_sheets_config()
    return str(Path(config.sqlite_storage_path) / f"{source_id}.db")


def invoke_hook_safely(
    hook: Optional[Callable[..., None]],
    environment_id: UUID,
    filename: str,
    **context: Any,
) -> None:
    """
    Safely invoke a lifecycle hook, catching and logging any errors.
    """
    if hook is None:
        return

    try:
        hook(environment_id=environment_id, filename=filename, **context)
    except Exception as exc:
        logger.warning(
            "File storage hook error: %s",
            exc,
            exc_info=True,
            extra={
                "hook": getattr(hook, "__name__", str(hook)),
                "environment_id": str(environment_id),
                "filename": filename,
            },
        )
