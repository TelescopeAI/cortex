from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from cortex.core import WorkspaceEnvironmentORM
from cortex.core.workspaces.db.workspace_service import WorkspaceCRUD
from cortex.core.workspaces.environments.environment import WorkspaceEnvironment
from cortex.core.exceptions.environments import (EnvironmentAlreadyExistsError, EnvironmentDoesNotExistError,
                                                 NoEnvironmentsExistError)
from cortex.core.exceptions.workspaces import WorkspaceDoesNotExistError
from cortex.core.storage.store import CortexStorage


class EnvironmentCRUD:

    @staticmethod
    def get_environment_by_name_and_workspace(
        name: str, 
        workspace_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> Optional[WorkspaceEnvironment]:
        """
        Get environment by name and workspace ID.
        
        Args:
            name: Environment name to search for
            workspace_id: Workspace ID to filter by
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            WorkspaceEnvironment object or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
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
    def add_environment(
        environment: WorkspaceEnvironment,
        storage: Optional[CortexStorage] = None
    ) -> WorkspaceEnvironment:
        """
        Add a new environment to a workspace.
        
        Args:
            environment: WorkspaceEnvironment object to create
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Created environment object
            
        Raises:
            WorkspaceDoesNotExistError: If workspace not found
            EnvironmentAlreadyExistsError: If environment already exists
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if workspace exists
            WorkspaceCRUD.get_workspace(environment.workspace_id, storage=storage)

            # Check if environment with same name exists in the workspace
            existing_environment = EnvironmentCRUD.get_environment_by_name_and_workspace(
                environment.name,
                environment.workspace_id,
                storage=storage
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
    def get_environments_by_workspace(
        workspace_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> List[WorkspaceEnvironment]:
        """
        Get all environments for a workspace.
        
        Args:
            workspace_id: Workspace ID to get environments for
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of environment objects
            
        Raises:
            WorkspaceDoesNotExistError: If workspace not found
            NoEnvironmentsExistError: If no environments found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if workspace exists
            WorkspaceCRUD.get_workspace(workspace_id, storage=storage)

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
    def get_environment(
        environment_id: UUID,
        storage: Optional[CortexStorage] = None
    ) -> WorkspaceEnvironment:
        """
        Get environment by ID.
        
        Args:
            environment_id: Environment ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            WorkspaceEnvironment object
            
        Raises:
            EnvironmentDoesNotExistError: If environment not found
        """
        db_session = (storage or CortexStorage()).get_session()
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
    def update_environment(
        environment: WorkspaceEnvironment,
        storage: Optional[CortexStorage] = None
    ) -> WorkspaceEnvironment:
        """
        Update an existing environment.
        
        Args:
            environment: WorkspaceEnvironment object with updated values
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Updated environment object
            
        Raises:
            EnvironmentDoesNotExistError: If environment not found
        """
        db_session = (storage or CortexStorage()).get_session()
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
    def delete_environment(
        environment: WorkspaceEnvironment,
        storage: Optional[CortexStorage] = None
    ) -> bool:
        """
        Delete an environment.
        
        Args:
            environment: WorkspaceEnvironment object to delete
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if environment was deleted, False otherwise
        """
        db_session = (storage or CortexStorage()).get_session()
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