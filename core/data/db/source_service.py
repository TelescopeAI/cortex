from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from core.data.db.sources import DataSourceORM
from core.data.sources.data_sources import DataSource
from core.exceptions.data.sources import DataSourceAlreadyExistsError, DataSourceDoesNotExistError
from core.stores.connection import LocalSession
from core.workspaces.db.environment_service import EnvironmentCRUD


class DataSourceCRUD:

    @staticmethod
    def get_data_source_by_name_and_environment(name: str, environment_id: UUID) -> Optional[DataSource]:
        db_session = LocalSession().get_session()
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
    def add_data_source(data_source: DataSource) -> DataSource:
        db_session = LocalSession().get_session()
        try:
            # Check if environment exists
            EnvironmentCRUD.get_environment(data_source.environment_id)

            # Check if data source with same name exists in the environment
            existing_source = DataSourceCRUD.get_data_source_by_name_and_environment(
                data_source.name,
                data_source.environment_id
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
    def get_data_source(data_source_id: UUID) -> DataSource:
        db_session = LocalSession().get_session()
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
    def get_data_sources_by_environment(environment_id: UUID) -> List[DataSource]:
        db_session = LocalSession().get_session()
        try:
            # Verify environment exists
            EnvironmentCRUD.get_environment(environment_id)

            db_data_sources = db_session.query(DataSourceORM).filter(
                DataSourceORM.environment_id == environment_id
            ).all()
            return [DataSource.model_validate(ds, from_attributes=True) for ds in db_data_sources]
        finally:
            db_session.close()

    @staticmethod
    def update_data_source(data_source: DataSource) -> DataSource:
        db_session = LocalSession().get_session()
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
    def delete_data_source(data_source_id: UUID) -> bool:
        db_session = LocalSession().get_session()
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