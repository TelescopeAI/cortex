import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from cortex.core.data.db.metric_service import MetricService
from cortex.core.data.db.models import MetricORM
from cortex.core.data.db.sources import DataSourceORM
from cortex.core.data.sources.data_sources import DataSource
from cortex.core.exceptions.data.sources import (
    DataSourceAlreadyExistsError,
    DataSourceDoesNotExistError,
    DataSourceHasDependenciesError
)
from cortex.core.storage.store import CortexStorage
from cortex.core.utils import data_sources
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD


class DataSourceCRUD:

    @staticmethod
    def get_data_source_by_name_and_environment(
        name: str,
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Optional[DataSource]:
        """
        Get data source by name and environment ID.
        
        Args:
            name: Data source name to search for
            environment_id: Environment ID to filter by
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            DataSource object or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_data_source = db_session.query(DataSourceORM).filter(
                DataSourceORM.name == name,
                DataSourceORM.environment_id == environment_id
            ).first()
            if db_data_source is None:
                return None
            return DataSource.model_validate(db_data_source, from_attributes=True)
        finally:
            db_session.close()

    @staticmethod
    def add_data_source(
        data_source: DataSource,
        storage: Optional[CortexStorage] = None
    ) -> DataSource:
        """
        Add a new data source to an environment.
        
        Args:
            data_source: DataSource object to create
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Created data source object
            
        Raises:
            DataSourceAlreadyExistsError: If data source already exists
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if environment exists
            EnvironmentCRUD.get_environment(data_source.environment_id, storage=storage)

            # Check if data source with same name exists in the environment
            existing_source = DataSourceCRUD.get_data_source_by_name_and_environment(
                data_source.name,
                data_source.environment_id,
                storage=storage
            )
            if existing_source:
                raise DataSourceAlreadyExistsError(data_source.name, data_source.environment_id)

            while True:
                try:
                    data_source_id = uuid4()
                    db_data_source = DataSourceORM(
                        id=data_source_id,
                        environment_id=data_source.environment_id,
                        name=data_source.name,
                        alias=data_source.alias,
                        description=data_source.description,
                        source_catalog=data_source.source_catalog.value,
                        source_type=data_source.source_type.value,
                        config=data_source.config,
                        created_at=datetime.now(pytz.UTC),
                        updated_at=datetime.now(pytz.UTC)
                    )
                    db_session.add(db_data_source)
                    db_session.commit()
                    db_session.refresh(db_data_source)
                    return DataSource.model_validate(db_data_source, from_attributes=True)
                except IntegrityError:
                    db_session.rollback()
                    continue
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_data_source(
        data_source_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> DataSource:
        """
        Get data source by ID.
        
        Args:
            data_source_id: Data source ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            DataSource object
            
        Raises:
            DataSourceDoesNotExistError: If data source not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_data_source = db_session.query(DataSourceORM).filter(
                DataSourceORM.id == data_source_id
            ).first()
            if db_data_source is None:
                raise DataSourceDoesNotExistError(data_source_id)
            return DataSource.model_validate(db_data_source, from_attributes=True)
        finally:
            db_session.close()

    @staticmethod
    def get_data_sources_by_environment(
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> List[DataSource]:
        """
        Get all data sources for an environment.
        
        Args:
            environment_id: Environment ID to get data sources for
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of data source objects
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Verify environment exists
            EnvironmentCRUD.get_environment(environment_id, storage=storage)

            db_data_sources = db_session.query(DataSourceORM).filter(
                DataSourceORM.environment_id == environment_id
            ).all()
            return [DataSource.model_validate(ds, from_attributes=True) for ds in db_data_sources]
        finally:
            db_session.close()

    @staticmethod
    def update_data_source(
        data_source: DataSource,
        storage: Optional[CortexStorage] = None
    ) -> DataSource:
        """
        Update an existing data source.
        
        Args:
            data_source: DataSource object with updated values
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Updated data source object
            
        Raises:
            DataSourceDoesNotExistError: If data source not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_data_source = db_session.query(DataSourceORM).filter(
                DataSourceORM.id == data_source.id
            ).first()
            if db_data_source is None:
                raise DataSourceDoesNotExistError(data_source.id)

            # Track if any changes were made
            changes_made = False

            # Check and update only allowed fields if they've changed
            if data_source.name != db_data_source.name:
                db_data_source.name = data_source.name
                changes_made = True

            if data_source.alias != db_data_source.alias:
                db_data_source.alias = data_source.alias
                changes_made = True

            if data_source.description != db_data_source.description:
                db_data_source.description = data_source.description
                changes_made = True

            if data_source.config != db_data_source.config:
                db_data_source.config = data_source.config
                changes_made = True

            # Only update if changes were made
            if changes_made:
                db_data_source.updated_at = datetime.now(pytz.UTC)
                db_session.commit()
                db_session.refresh(db_data_source)

            return DataSource.model_validate(db_data_source, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_data_source_dependencies(
        data_source_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Dict[str, Any]:
        """
        Get all entities that depend on a data source.

        Args:
            data_source_id: Data source ID to check
            storage: Optional CortexStorage instance

        Returns:
            Dictionary with dependency information:
            {
                "metrics": [{"id": UUID, "name": str, "alias": str, "version_count": int}, ...]
            }
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            dependent_metrics = db_session.query(MetricORM).filter(
                MetricORM.data_source_id == data_source_id
            ).all()

            # Create MetricService instance to get version counts
            metric_service = MetricService(session=db_session)

            return {
                "metrics": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "alias": m.alias,
                        "version_count": metric_service.get_metric_version_count(m.id)
                    }
                    for m in dependent_metrics
                ]
            }
        finally:
            db_session.close()

    @staticmethod
    def delete_data_source(
        data_source_id: UUID,
        cascade: bool = False,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Delete a data source.

        Args:
            data_source_id: Data source ID to delete
            cascade: If True, delete all dependent metrics (and their versions) first
            storage: Optional CortexStorage instance

        Returns:
            True if data source was deleted

        Raises:
            DataSourceDoesNotExistError: If data source not found
            DataSourceHasDependenciesError: If cascade=False and dependencies exist
        """
        storage_instance = storage or CortexStorage()
        db_session = storage_instance.get_session()
        try:
            # Verify data source exists
            db_data_source = db_session.query(DataSourceORM).filter(
                DataSourceORM.id == data_source_id
            ).first()
            if db_data_source is None:
                raise DataSourceDoesNotExistError(data_source_id)

            # Check for dependencies
            dependent_metrics = db_session.query(MetricORM).filter(
                MetricORM.data_source_id == data_source_id
            ).all()

            if len(dependent_metrics) > 0:
                if not cascade:
                    raise DataSourceHasDependenciesError(
                        data_source_id=data_source_id,
                        metric_ids=[m.id for m in dependent_metrics]
                    )

                # CASCADE: Delete dependent metrics and their versions using MetricService
                # MetricService.delete_metric() properly handles cascade deletion of metric_versions
                metric_service = MetricService(session=db_session)
                for metric in dependent_metrics:
                    metric_service.delete_metric(metric.id)

            # Clean up physical files before deleting database record
            config = db_data_source.config
            sqlite_path = config.get('sqlite_path')
            file_id = config.get('file_id')

            # Import here to avoid circular dependency
            from cortex.core.services.data.sources.files import FileStorageService

            # Use existing FileStorageService to get the appropriate storage backend
            file_service = FileStorageService()
            storage_backend = file_service.storage_backend

            # 1. Delete SQLite database file (with cache cleanup if GCS)
            if sqlite_path:
                source_identifier = str(db_data_source.alias or db_data_source.name)
                data_sources.delete_sqlite_with_cache_cleanup(
                    sqlite_path=sqlite_path,
                    source_identifier=source_identifier,
                    storage_backend=storage_backend
                )

            # 2. Delete input CSV file if it exists and no other data sources depend on it
            if file_id:
                # Import here to avoid circular dependency
                from cortex.core.data.db.sources import CortexFileStorageORM

                # Check if other data sources depend on this file
                file_id_uuid = UUID(str(file_id))

                # Query all data sources except current one and check config in Python
                # (more compatible across databases than JSON field accessors)
                all_sources = db_session.query(DataSourceORM).filter(
                    DataSourceORM.id != db_data_source.id
                ).all()

                dependent_sources = sum(
                    1 for ds in all_sources
                    if ds.config and ds.config.get('file_id') == str(file_id_uuid)
                )

                # Only delete the input file if no other data sources depend on it
                if dependent_sources == 0:
                    file_record = db_session.query(CortexFileStorageORM).filter(
                        CortexFileStorageORM.id == file_id_uuid
                    ).first()
                    if file_record:
                        data_sources.delete_input_file_with_cleanup(
                            encrypted_file_path=file_record.path,
                            storage_backend=storage_backend
                        )

            # Delete the data source
            db_session.delete(db_data_source)
            db_session.commit()
            return True

        except (DataSourceDoesNotExistError, DataSourceHasDependenciesError):
            db_session.rollback()
            raise
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()