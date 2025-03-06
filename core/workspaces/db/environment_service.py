from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from core import WorkspaceEnvironmentORM
from core.workspaces.db.workspace_service import WorkspaceCRUD
from core.workspaces.environments.environment import WorkspaceEnvironment
from core.exceptions.environments import (EnvironmentAlreadyExistsError, EnvironmentDoesNotExistError,
                                          NoEnvironmentsExistError)
from core.exceptions.workspaces import WorkspaceDoesNotExistError
from core.stores.connection import LocalSession


class EnvironmentCRUD:

    @staticmethod
    def get_environment_by_name_and_workspace(name: str, workspace_id: UUID) -> Optional[WorkspaceEnvironment]:
        db_session = LocalSession().get_session()
        try:
            db_environment = db_session.query(WorkspaceEnvironmentORM).filter(
                WorkspaceEnvironmentORM.name == name,
                WorkspaceEnvironmentORM.workspace_id == workspace_id
            ).first()
            if db_environment is None:
                return None
            return WorkspaceEnvironment.model_validate(db_environment, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def add_environment(environment: WorkspaceEnvironment) -> WorkspaceEnvironment:
        db_session = LocalSession().get_session()
        try:
            # Check if workspace exists
            WorkspaceCRUD.get_workspace(environment.workspace_id)

            # Check if environment with same name exists in the workspace
            existing_environment = EnvironmentCRUD.get_environment_by_name_and_workspace(
                environment.name,
                environment.workspace_id
            )
            if existing_environment:
                raise EnvironmentAlreadyExistsError(environment.name, environment.workspace_id)

            while True:
                try:
                    environment_id = uuid4()
                    db_environment = WorkspaceEnvironmentORM(
                        id=environment_id,
                        workspace_id=environment.workspace_id,
                        name=environment.name,
                        description=environment.description,
                        created_at=datetime.now(pytz.UTC),
                        updated_at=datetime.now(pytz.UTC)
                    )
                    db_session.add(db_environment)
                    db_session.commit()
                    db_session.refresh(db_environment)
                    return WorkspaceEnvironment.model_validate(db_environment, from_attributes=True)
                except IntegrityError:
                    db_session.rollback()
                    continue
        except (WorkspaceDoesNotExistError, EnvironmentAlreadyExistsError) as e:
            raise e
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_environments_by_workspace(workspace_id: UUID) -> List[WorkspaceEnvironment]:
        db_session = LocalSession().get_session()
        try:
            # Check if workspace exists
            WorkspaceCRUD.get_workspace(workspace_id)

            db_environments = db_session.query(WorkspaceEnvironmentORM).filter(
                WorkspaceEnvironmentORM.workspace_id == workspace_id
            ).all()
            if not db_environments:
                raise NoEnvironmentsExistError(f"No environments found for workspace {workspace_id}")
            return [WorkspaceEnvironment.model_validate(env, from_attributes=True) for env in db_environments]
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_environment(environment_id: UUID) -> WorkspaceEnvironment:
        db_session = LocalSession().get_session()
        try:
            db_environment = db_session.query(WorkspaceEnvironmentORM).filter(
                WorkspaceEnvironmentORM.id == environment_id
            ).first()
            if db_environment is None:
                raise EnvironmentDoesNotExistError(environment_id)
            return WorkspaceEnvironment.model_validate(db_environment, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def update_environment(environment: WorkspaceEnvironment) -> WorkspaceEnvironment:
        db_session = LocalSession().get_session()
        try:
            db_environment = db_session.query(WorkspaceEnvironmentORM).filter(
                WorkspaceEnvironmentORM.id == environment.id
            ).first()
            if db_environment is None:
                raise EnvironmentDoesNotExistError(environment.id)

            db_environment.name = environment.name
            db_environment.description = environment.description
            db_environment.updated_at = datetime.now(pytz.UTC)

            db_session.commit()
            db_session.refresh(db_environment)
            return WorkspaceEnvironment.model_validate(db_environment, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def delete_environment(environment: WorkspaceEnvironment) -> bool:
        db_session = LocalSession().get_session()
        try:
            result = db_session.query(WorkspaceEnvironmentORM).filter(
                WorkspaceEnvironmentORM.id == environment.id
            ).delete()
            db_session.commit()
            return result > 0
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()