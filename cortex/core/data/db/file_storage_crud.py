"""
File storage CRUD operations.

Pure database operations only - no business logic.
Handles insert, query, update, delete, and dependency tracking.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from cortex.core.data.db.sources import CortexFileStorageORM, DataSourceORM
from cortex.core.data.sources.data_sources import CortexFileStorage
from cortex.core.storage.store import CortexStorage


class FileStorageCRUD:
    """Pure database CRUD operations for file storage"""

    @staticmethod
    def create(
        file: CortexFileStorage,
        storage: Optional[CortexStorage] = None
    ) -> CortexFileStorage:
        """
        Insert file record into database.

        Args:
            file: Pydantic model (TSModel) with all fields populated
            storage: Optional CortexStorage instance

        Returns:
            Pydantic model validated from DB record
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Convert Pydantic to ORM
            file_record = CortexFileStorageORM(
                id=file.id,
                environment_id=file.environment_id,
                name=file.name,
                extension=file.extension,
                size=file.size,
                mime_type=file.mime_type,
                hash=file.hash,
                path=file.path,  # Should already be encrypted by Service
                created_at=file.created_at,
                updated_at=file.updated_at
            )

            db_session.add(file_record)
            db_session.commit()
            db_session.refresh(file_record)

            return CortexFileStorage.model_validate(file_record, from_attributes=True)
        except IntegrityError:
            db_session.rollback()
            raise
        finally:
            db_session.close()

    @staticmethod
    def get_by_id(
        file_id: UUID,
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Optional[CortexFileStorage]:
        """
        Query file by ID with environment validation.

        Args:
            file_id: File ID
            environment_id: Environment ID for security validation
            storage: Optional CortexStorage instance

        Returns:
            Pydantic model or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            file_record = db_session.query(CortexFileStorageORM).filter_by(
                id=file_id,
                environment_id=environment_id
            ).first()

            if not file_record:
                return None

            return CortexFileStorage.model_validate(file_record, from_attributes=True)
        finally:
            db_session.close()

    @staticmethod
    def list_by_environment(
        environment_id: UUID,
        limit: Optional[int] = None,
        storage: Optional[CortexStorage] = None
    ) -> List[CortexFileStorage]:
        """
        Query all files in environment.

        Args:
            environment_id: Environment ID
            limit: Optional limit on number of files
            storage: Optional CortexStorage instance

        Returns:
            List of Pydantic models
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            query = db_session.query(CortexFileStorageORM).filter_by(
                environment_id=environment_id
            ).order_by(CortexFileStorageORM.created_at.desc())

            if limit:
                query = query.limit(limit)

            records = query.all()
            return [
                CortexFileStorage.model_validate(r, from_attributes=True)
                for r in records
            ]
        finally:
            db_session.close()

    @staticmethod
    def delete(
        file_id: UUID,
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Delete file record from database.

        Args:
            file_id: File ID to delete
            environment_id: Environment ID for security validation
            storage: Optional CortexStorage instance

        Returns:
            True if deleted, False if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            file_record = db_session.query(CortexFileStorageORM).filter(
                CortexFileStorageORM.id == file_id,
                CortexFileStorageORM.environment_id == environment_id
            ).first()

            if not file_record:
                return False

            db_session.delete(file_record)
            db_session.commit()
            return True
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()

    @staticmethod
    def get_dependencies(
        file_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Dict[str, Any]:
        """
        Query dependency tree: File → DataSources → Metrics.

        Args:
            file_id: File ID
            storage: Optional CortexStorage instance

        Returns:
            {
                "data_sources": [
                    {
                        "id": UUID,
                        "name": str,
                        "alias": str,
                        "metrics": [...]
                    }
                ]
            }
        """
        from cortex.core.data.db.source_service import DataSourceCRUD

        db_session = (storage or CortexStorage()).get_session()
        try:
            # Query data sources where config['file_id'] matches
            # Use path-based indexing for dialect-independent JSON querying
            # This works across PostgreSQL, MySQL, and SQLite
            dependent_data_sources = db_session.query(DataSourceORM).filter(
                DataSourceORM.config["file_id"].as_string() == str(file_id)
            ).all()

            result_data_sources = []
            for ds in dependent_data_sources:
                # Get metrics for each data source
                ds_deps = DataSourceCRUD.get_data_source_dependencies(ds.id, storage=storage)
                result_data_sources.append({
                    "id": ds.id,
                    "name": ds.name,
                    "alias": ds.alias,
                    "metrics": ds_deps["metrics"]
                })

            return {"data_sources": result_data_sources}
        finally:
            db_session.close()
