"""Utility functions for data source file deletion and storage cleanup."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from cortex.core.connectors.api.sheets.storage.base import CortexFileStorageBackend


def cleanup_empty_directories(start_dir: Path, base_paths: Set[Path]) -> None:
    """
    Recursively remove empty directories up the hierarchy.

    This is a shared utility that can be used by both local storage backend
    and cache manager to clean up empty workspace/environment directories.

    Args:
        start_dir: Starting directory to check and remove if empty
        base_paths: Set of base paths where cleanup should stop
    """
    logger = logging.getLogger(__name__)
    current_dir = start_dir

    # Walk up the directory tree
    while current_dir not in base_paths and current_dir != current_dir.parent:
        try:
            # rmdir() only succeeds if directory is empty
            # Automatically fails if hidden files present
            current_dir.rmdir()
            logger.info(f"Removed empty directory: {current_dir}")
            current_dir = current_dir.parent
        except OSError as e:
            # Directory not empty, doesn't exist, or permission error
            # This is expected for non-empty directories - just stop trying
            if current_dir.exists():
                # Directory exists but not empty (probably has other files)
                logger.debug(f"Directory not empty, stopping cleanup: {current_dir} (reason: {e})")
            else:
                logger.debug(f"Directory does not exist, stopping cleanup: {current_dir}")
            break
        except PermissionError as e:
            # Permission issue - this is unusual and should be logged as warning
            logger.warning(f"Permission denied when trying to remove directory: {current_dir} - {e}")
            break


def delete_sqlite_with_cache_cleanup(
    sqlite_path: str,
    source_identifier: str,
    storage_backend: "CortexFileStorageBackend"
) -> bool:
    """
    Delete SQLite file and clean cache metadata if GCS.

    Args:
        sqlite_path: Path to SQLite file (local path or gs:// URI)
        source_identifier: Source ID or alias for cache lookup
        storage_backend: Storage backend instance to use for deletion

    Returns:
        True if file was deleted, False if not found
    """
    if not sqlite_path:
        return False

    # Delete from storage backend
    deleted = storage_backend.delete_sqlite(sqlite_path)

    # If GCS, also clean cache metadata
    if sqlite_path.startswith('gs://'):
        try:
            # Lazy imports to avoid circular dependencies
            from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
            from cortex.core.connectors.api.sheets.config import get_sheets_config

            sheets_config = get_sheets_config()
            cache_manager = CortexFileStorageCacheManager(
                cache_dir=sheets_config.cache_dir,
                sqlite_dir=sheets_config.sqlite_storage_path,
                max_size_gb=sheets_config.cache_max_size_gb
            )
            cache_manager.delete_cache_entry(source_identifier)
        except Exception as e:
            print(f"Warning: Could not clean cache metadata: {e}")

    return deleted


def delete_input_file_with_cleanup(
    encrypted_file_path: str,
    storage_backend: Optional["CortexFileStorageBackend"] = None
) -> bool:
    """
    Delete input CSV file and clean up empty directories.

    Args:
        encrypted_file_path: Encrypted file path string
        storage_backend: Optional storage backend for directory cleanup

    Returns:
        True if file was deleted, False if not found or error
    """
    try:
        # Lazy import to avoid circular dependencies
        from cortex.core.utils.encryption import FilePathEncryption

        # Decrypt the file path
        file_path = FilePathEncryption.decrypt(encrypted_file_path)

        if not os.path.exists(file_path):
            return False

        # Delete the file
        os.remove(file_path)
        print(f"Deleted input file: {file_path}")

        # Clean up empty parent directories
        if storage_backend and hasattr(storage_backend, '_cleanup_empty_directories'):
            storage_backend._cleanup_empty_directories(Path(file_path).parent)

        return True

    except Exception as e:
        print(f"Warning: Could not delete input file: {e}")
        return False
