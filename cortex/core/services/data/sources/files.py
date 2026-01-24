"""File storage service for managing uploaded files"""
import os
import hashlib
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

import pytz
import magic

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.connectors.api.sheets.config import get_sheets_config
from cortex.core.connectors.api.sheets.types import CortexSheetsStorageType
from cortex.core.data.db.sources import CortexFileStorageORM
from cortex.core.data.sources.data_sources import CortexFileStorage
from cortex.core.storage.store import CortexStorage
from cortex.core.utils.encryption import FilePathEncryption
from cortex.core.connectors.api.sheets.storage.local import CortexLocalFileStorage
from cortex.core.connectors.api.sheets.exceptions import StorageFileAlreadyExists
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.core.services.data.sources.files_config import (
    get_file_storage_config,
    invoke_hook_safely,
    default_upload_path_generator,
    UploadPathGeneratorConfig,
    SqlitePathGeneratorConfig,
    HookInvokerConfig,
)


class FileStorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        # Auto-select storage backend based on config
        config = get_sheets_config()
        
        if config.storage_type == CortexSheetsStorageType.GCS:
            from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
            from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend
            
            cache_manager = CortexFileStorageCacheManager(
                cache_dir=config.cache_dir,
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
        Upload a single file with duplicate detection
        
        Args:
            environment_id: Environment ID for multi-tenancy
            filename: Original filename with extension
            content: File content as bytes
            overwrite: Whether to overwrite existing file
            
        Returns:
            CortexFileStorage model with file metadata
            
        Raises:
            StorageFileAlreadyExists: If file exists and overwrite=False
        """
        config = get_file_storage_config()
        storage_config = get_sheets_config()
        session = CortexStorage().get_session()

        try:
            # Get workspace_id from environment
            environment = EnvironmentCRUD.get_environment(
                storage=CortexStorage(),
                environment_id=environment_id
            )
            if not environment:
                raise ValueError(f"Environment {environment_id} not found")
            workspace_id = environment.workspace_id

            # Extract name and extension
            name, extension = os.path.splitext(filename)
            extension = extension.lstrip('.')

            # Detect MIME type and calculate hash
            mime_type = magic.from_buffer(content, mime=True)
            file_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

            # Create hook config for upload_start
            hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=filename,
                event_type="upload_start",
                file_size=file_size,
                mime_type=mime_type,
                meta={"hash": file_hash, "overwrite": overwrite}
            )
            invoke_hook_safely(config.on_upload_start, hook_config)

            # Check for existing file
            existing = session.query(CortexFileStorageORM).filter_by(
                environment_id=environment_id,
                name=name,
                extension=extension
            ).first()

            if existing and not overwrite:
                raise StorageFileAlreadyExists(filename, str(existing.id))

            # Build config for path generation
            path_config = UploadPathGeneratorConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=name,
                extension=extension,
                source_id=None,
                base_storage_path=storage_config.input_storage_path,
                file_size=file_size,
                mime_type=mime_type
            )
            
            # Call path generator with config
            path_generator = config.upload_path_generator or default_upload_path_generator
            file_path = self.storage_backend.save_file(
                source_id=str(uuid4()),
                filename=filename,
                data=content,
                overwrite=overwrite,
                path_generator=lambda source_id, _filename: path_generator(path_config),
            )

            # Encrypt path
            encrypted_path = FilePathEncryption.encrypt(file_path)

            # Create or update database record
            if existing:
                existing.size = file_size
                existing.path = encrypted_path
                existing.hash = file_hash
                existing.mime_type = mime_type
                existing.updated_at = datetime.now(pytz.UTC)
                file_record = existing
            else:
                file_record = CortexFileStorageORM(
                    environment_id=environment_id,
                    name=name,
                    mime_type=mime_type,
                    extension=extension,
                    size=file_size,
                    path=encrypted_path,
                    hash=file_hash
                )
                session.add(file_record)

            session.commit()
            session.refresh(file_record)

            # Create hook config for upload_success
            success_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=filename,
                event_type="upload_success",
                file_id=file_record.id,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
            )
            invoke_hook_safely(config.on_upload_success, success_hook_config)

            return CortexFileStorage(
                id=file_record.id,
                environment_id=file_record.environment_id,
                name=file_record.name,
                mime_type=file_record.mime_type,
                extension=file_record.extension,
                size=file_record.size,
                path=file_path,
                hash=file_record.hash,
                created_at=file_record.created_at,
                updated_at=file_record.updated_at
            )
        except StorageFileAlreadyExists as exc:
            error_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=filename,
                event_type="upload_error",
                file_size=file_size,
                mime_type=mime_type,
                error=exc,
                meta={"error_type": type(exc).__name__}
            )
            invoke_hook_safely(config.on_upload_error, error_hook_config)
            raise
        except Exception as exc:
            error_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=filename,
                event_type="upload_error",
                error=exc,
                meta={"error_type": type(exc).__name__}
            )
            invoke_hook_safely(config.on_upload_error, error_hook_config)
            raise
        finally:
            session.close()
    
    def upload_files(
        self,
        environment_id: UUID,
        files: List[tuple[str, bytes]],  # [(filename, content), ...]
        overwrite: bool = False
    ) -> List[CortexFileStorage]:
        """
        Upload multiple files
        
        Args:
            environment_id: Environment ID for multi-tenancy
            files: List of (filename, content) tuples
            overwrite: Whether to overwrite existing files
            
        Returns:
            List of CortexFileStorage models
        """
        uploaded_files = []
        
        for filename, content in files:
            file_model = self.upload_file(
                environment_id=environment_id,
                filename=filename,
                content=content,
                overwrite=overwrite
            )
            uploaded_files.append(file_model)
        
        return uploaded_files
    
    def list_files(
        self,
        environment_id: UUID,
        limit: Optional[int] = None
    ) -> List[CortexFileStorage]:
        """
        List all uploaded files for an environment
        
        Args:
            environment_id: Environment ID to filter by
            limit: Optional limit on number of results
            
        Returns:
            List of CortexFileStorage models
        """
        session = CortexStorage().get_session()
        
        try:
            query = session.query(CortexFileStorageORM).filter_by(
                environment_id=environment_id
            ).order_by(CortexFileStorageORM.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            files = query.all()
            
            # Convert to Pydantic models (decrypt paths)
            return [
                CortexFileStorage(
                    id=f.id,
                    environment_id=f.environment_id,
                    name=f.name,
                    mime_type=f.mime_type,
                    extension=f.extension,
                    size=f.size,
                    path=FilePathEncryption.decrypt(f.path),
                    hash=f.hash,
                    created_at=f.created_at,
                    updated_at=f.updated_at
                )
                for f in files
            ]
        finally:
            session.close()
    
    def get_file(
        self,
        file_id: UUID,
        environment_id: UUID
    ) -> Optional[CortexFileStorage]:
        """
        Get a single file by ID
        
        Args:
            file_id: File ID
            environment_id: Environment ID for security
            
        Returns:
            CortexFileStorage model or None
        """
        session = CortexStorage().get_session()
        
        try:
            file_record = session.query(CortexFileStorageORM).filter_by(
                id=file_id,
                environment_id=environment_id
            ).first()
            
            if not file_record:
                return None
            
            return CortexFileStorage(
                id=file_record.id,
                environment_id=file_record.environment_id,
                name=file_record.name,
                mime_type=file_record.mime_type,
                extension=file_record.extension,
                size=file_record.size,
                path=FilePathEncryption.decrypt(file_record.path),
                hash=file_record.hash,
                created_at=file_record.created_at,
                updated_at=file_record.updated_at
            )
        finally:
            session.close()
    
    def delete_file(
        self,
        file_id: UUID,
        environment_id: UUID
    ) -> bool:
        """
        Delete a file from storage and database
        
        Args:
            file_id: File ID
            environment_id: Environment ID for security
            
        Returns:
            True if deleted, False if not found
        """
        config = get_file_storage_config()
        session = CortexStorage().get_session()

        try:
            # Get workspace_id from environment
            environment = EnvironmentCRUD.get_environment(
                storage=CortexStorage(),
                environment_id=environment_id
            )
            if not environment:
                raise ValueError(f"Environment {environment_id} not found")
            workspace_id = environment.workspace_id

            file_record = session.query(CortexFileStorageORM).filter_by(
                id=file_id,
                environment_id=environment_id
            ).first()

            if not file_record:
                return False

            display_name = f"{file_record.name}.{file_record.extension}"
            
            # Create hook config for delete_start
            delete_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=display_name,
                event_type="delete_start",
                file_id=file_id,
            )
            invoke_hook_safely(config.on_delete_start, delete_hook_config)

            # Decrypt path and delete physical file
            file_path = FilePathEncryption.decrypt(file_record.path)
            if os.path.exists(file_path):
                os.remove(file_path)

            # Delete database record
            session.delete(file_record)
            session.commit()

            # Create hook config for delete_success
            success_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=display_name,
                event_type="delete_success",
                file_id=file_id,
                file_path=file_path,
            )
            invoke_hook_safely(config.on_delete_success, success_hook_config)

            return True
        except Exception as exc:
            fallback_name = display_name if "display_name" in locals() else "unknown"
            error_hook_config = HookInvokerConfig(
                workspace_id=workspace_id,
                environment_id=environment_id,
                filename=fallback_name,
                event_type="delete_error",
                file_id=file_id,
                error=exc,
            )
            invoke_hook_safely(config.on_delete_error, error_hook_config)
            raise
        finally:
            session.close()
