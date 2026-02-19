"""
File storage service for managing uploaded files.

Business logic orchestration for file storage operations including:
- File uploads with MIME detection and hash calculation
- Duplicate detection
- Physical file storage (Local or GCS)
- Path generation and encryption
- Hook invocation
- Cache management
- Uses FileStorageCRUD for database operations
"""
import os
import hashlib
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

import pytz
import magic

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.core.connectors.api.sheets.types import CortexSheetsStorageType
from cortex.core.connectors.api.sheets.storage.local import CortexLocalFileStorage
from cortex.core.connectors.api.sheets.exceptions import StorageFileAlreadyExists
from cortex.core.data.db.file_storage_crud import FileStorageCRUD
from cortex.core.data.db.sources import CortexFileStorageORM
from cortex.core.data.sources.data_sources import CortexFileStorage
from cortex.core.exceptions.data.sources import (
    FileDoesNotExistError,
    FileHasDependenciesError
)
from cortex.core.storage.store import CortexStorage
from cortex.core.utils.encryption import FilePathEncryption
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.core.services.data.sources.files_config import (
    get_file_storage_config,
    default_upload_path_generator,
    UploadPathGeneratorConfig,
)


class FileStorageService:
    """Business logic orchestration for file storage operations"""

    def __init__(self):
        """Initialize with storage backend (Local or GCS)"""
        config = get_sheets_config()

        if config.storage_type == CortexSheetsStorageType.GCS:
            from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
            from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend

            cache_manager = CortexFileStorageCacheManager(
                cache_dir=config.cache_dir,
                sqlite_dir=config.sqlite_storage_path,
                max_size_gb=config.cache_max_size_gb
            )

            self.storage_backend = CortexFileStorageGCSBackend(
                bucket_name=config.gcs_bucket,
                prefix=config.gcs_prefix,
                cache_manager=cache_manager
            )
        else:
            self.storage_backend = CortexLocalFileStorage()

    def upload_file(
        self,
        environment_id: UUID,
        filename: str,
        content: bytes,
        overwrite: bool = False
    ) -> CortexFileStorage:
        """
        Upload file with full business logic.

        Steps:
        1. Validate environment exists
        2. Detect MIME type
        3. Calculate file hash
        4. Check duplicates
        5. Generate storage path
        6. Upload to storage backend
        7. Encrypt path
        8. Create DB record via FileStorageCRUD
        9. Invoke success hook

        Args:
            environment_id: Environment ID for multi-tenancy
            filename: Original filename with extension
            content: File content as bytes
            overwrite: Whether to overwrite existing file

        Returns:
            CortexFileStorage model with file metadata

        Raises:
            StorageFileAlreadyExists: If file exists and overwrite=False
            ValueError: If environment not found
        """
        config = get_file_storage_config()

        # 1. Validate environment
        environment = EnvironmentCRUD.get_environment(environment_id=environment_id)
        if not environment:
            raise ValueError(f"Environment {environment_id} not found")
        workspace_id = environment.workspace_id

        # 2-3. Detect MIME type and calculate hash
        name, extension = os.path.splitext(filename)
        extension = extension.lstrip('.')
        mime_type = magic.from_buffer(content, mime=True)
        file_hash = hashlib.sha256(content).hexdigest()
        file_size = len(content)

        # 4. Check duplicates
        existing_files = FileStorageCRUD.list_by_environment(environment_id)
        for existing in existing_files:
            if existing.hash == file_hash:
                if not overwrite:
                    raise StorageFileAlreadyExists(
                        filename=filename,
                        existing_file_id=str(existing.id),
                        message=f"File '{filename}' already exists"
                    )
                # Delete existing if overwrite
                FileStorageCRUD.delete(existing.id, environment_id)

        # 5. Generate storage path and upload via backend
        file_id = uuid4()
        sheets_config = get_sheets_config()
        path_gen_config = UploadPathGeneratorConfig(
            workspace_id=workspace_id,
            environment_id=environment_id,
            filename=filename,
            extension=extension,
            source_id=str(file_id),
            base_storage_path=sheets_config.input_storage_path,
            file_size=file_size,
            mime_type=mime_type,
        )
        path_generator_func = config.upload_path_generator or default_upload_path_generator
        target_path = path_generator_func(path_gen_config)

        # Create adapter for save_file's path_generator signature
        def adapted_path_generator(source_id: str, fname: str) -> str:
            return target_path

        # 6. Upload to storage backend using save_file
        storage_path = self.storage_backend.save_file(
            source_id=str(file_id),
            filename=f"{filename}.{extension}" if extension else filename,
            data=content,
            overwrite=False,  # We already handled duplicates above
            path_generator=adapted_path_generator
        )

        # 7. Encrypt path
        encrypted_path = FilePathEncryption.encrypt(storage_path)

        # 8. Create DB record (Pydantic model, CRUD handles ORM conversion)
        file_model = CortexFileStorage(
            id=file_id,
            environment_id=environment_id,
            name=name,
            extension=extension,
            size=file_size,
            mime_type=mime_type,
            hash=file_hash,
            path=encrypted_path,
            created_at=datetime.now(pytz.UTC),
            updated_at=datetime.now(pytz.UTC)
        )

        created_file = FileStorageCRUD.create(file_model)

        # Return with decrypted path
        created_file.path = storage_path
        return created_file

    def upload_files(
        self,
        environment_id: UUID,
        files: List[Tuple[str, bytes]],
        overwrite: bool = False
    ) -> List[CortexFileStorage]:
        """
        Upload multiple files.

        Args:
            environment_id: Environment ID
            files: List of (filename, content) tuples
            overwrite: Whether to overwrite existing files

        Returns:
            List of CortexFileStorage models
        """
        uploaded_files = []
        for filename, content in files:
            file_record = self.upload_file(environment_id, filename, content, overwrite)
            uploaded_files.append(file_record)
        return uploaded_files

    def list_files(
        self,
        environment_id: UUID,
        limit: Optional[int] = None
    ) -> List[CortexFileStorage]:
        """
        List files with decrypted paths.

        Args:
            environment_id: Environment ID
            limit: Optional limit on number of files

        Returns:
            List of CortexFileStorage models with decrypted paths
        """
        files = FileStorageCRUD.list_by_environment(environment_id, limit)

        # Decrypt paths before returning
        for file in files:
            file.path = FilePathEncryption.decrypt(file.path)

        return files

    def get_file(
        self,
        file_id: UUID,
        environment_id: UUID
    ) -> CortexFileStorage:
        """
        Get file with decrypted path.

        Args:
            file_id: File ID
            environment_id: Environment ID for security validation

        Returns:
            CortexFileStorage model with decrypted path

        Raises:
            FileDoesNotExistError: If file not found
        """
        file = FileStorageCRUD.get_by_id(file_id, environment_id)
        if not file:
            raise FileDoesNotExistError(file_id)

        # Decrypt path
        file.path = FilePathEncryption.decrypt(file.path)
        return file

    def get_dependencies(
        self,
        file_id: UUID
    ) -> Dict[str, Any]:
        """
        Get file dependencies.

        Args:
            file_id: File ID

        Returns:
            Dictionary with dependency tree: File → DataSources → Metrics
        """
        return FileStorageCRUD.get_dependencies(file_id)

    def delete_file(
        self,
        file_id: UUID,
        environment_id: UUID,
        cascade: bool = False
    ) -> bool:
        """
        Delete file with cascade support.

        Steps:
        1. Get file record
        2. Get dependencies
        3. If dependencies exist and not cascade: raise error
        4. If cascade: delete data sources
        5. Invoke delete_start hook
        6. Clean SQLite cache if applicable
        7. Delete physical file (storage backend)
        8. Delete DB record
        9. Invoke delete_success hook

        Args:
            file_id: File ID to delete
            environment_id: Environment ID
            cascade: If true, delete dependent data sources and metrics

        Returns:
            True if deleted successfully

        Raises:
            FileDoesNotExistError: If file not found
            FileHasDependenciesError: If cascade=False and dependencies exist
        """
        from cortex.core.data.db.source_service import DataSourceCRUD

        config = get_file_storage_config()

        # 1. Get file record
        file_record = FileStorageCRUD.get_by_id(file_id, environment_id)
        if not file_record:
            raise FileDoesNotExistError(file_id)

        # Get workspace for hooks
        environment = EnvironmentCRUD.get_environment(environment_id=environment_id)
        workspace_id = environment.workspace_id if environment else None
        display_name = f"{file_record.name}.{file_record.extension}"

        # 2. Get dependencies
        dependencies = FileStorageCRUD.get_dependencies(file_id)
        dependent_data_sources = dependencies["data_sources"]

        # 3. Check cascade
        if len(dependent_data_sources) > 0:
            if not cascade:
                total_metrics = sum(len(ds["metrics"]) for ds in dependent_data_sources)
                raise FileHasDependenciesError(
                    file_id=file_id,
                    data_source_ids=[ds["id"] for ds in dependent_data_sources],
                    metric_count=total_metrics
                )

            # 4. Cascade delete
            for ds in dependent_data_sources:
                DataSourceCRUD.delete_data_source(ds["id"], cascade=True)

        # 5. Clean SQLite cache
        file_path = FilePathEncryption.decrypt(file_record.path)
        if file_path.endswith('.db'):
            try:
                import sqlite3
                from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager

                sheets_config = get_sheets_config()
                cache_manager = CortexFileStorageCacheManager(
                    cache_dir=sheets_config.cache_dir,
                    sqlite_dir=sheets_config.sqlite_storage_path,
                    max_size_gb=sheets_config.cache_max_size_gb
                )
                conn = sqlite3.connect(cache_manager.metadata_db)
                conn.execute(
                    "DELETE FROM files_cache_entries WHERE file_id = ?",
                    (str(file_id),)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Warning: Failed to clean cache for file {file_id}: {e}")

        # 7. Delete physical file
        if os.path.exists(file_path):
            os.remove(file_path)

        # 8. Delete DB record
        FileStorageCRUD.delete(file_id, environment_id)

        return True
