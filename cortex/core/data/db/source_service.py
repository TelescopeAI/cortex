from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from cortex.core.data.db.sources import DataSourceORM
from cortex.core.data.sources.data_sources import DataSource
from cortex.core.exceptions.data.sources import DataSourceAlreadyExistsError, DataSourceDoesNotExistError
from cortex.core.storage.store import CortexStorage
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
    def delete_data_source(
        data_source_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Delete a data source.
        
        Args:
            data_source_id: Data source ID to delete
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if data source was deleted, False otherwise
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            result = db_session.query(DataSourceORM).filter(
                DataSourceORM.id == data_source_id
            ).delete()
            db_session.commit()
            return result > 0
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()