from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.exc import IntegrityError

from cortex.core.exceptions.workspaces import WorkspaceDoesNotExistError, NoWorkspacesExistError, WorkspaceAlreadyExistsError
from cortex.core.storage.store import CortexStorage
from cortex.core.types.telescope import TSModel
from cortex.core.workspaces.workspace import Workspace
from cortex.core.workspaces.db.workspace import WorkspaceORM


class WorkspaceCRUD(TSModel):

    @staticmethod
    def get_workspace_by_name(name: str) -> Optional[Workspace]:
        db_session = CortexStorage().get_session()
        try:
            db_workspace = db_session.query(WorkspaceORM).filter(
                WorkspaceORM.name == name
            ).first()
            if db_workspace is None:
                return None
            return Workspace.model_validate(db_workspace, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def add_workspace(workspace: Workspace) -> Workspace:
        db_session = CortexStorage().get_session()
        try:
            # Check if workspace with same name exists
            existing_workspace = WorkspaceCRUD.get_workspace_by_name(workspace.name)
            if existing_workspace:
                raise WorkspaceAlreadyExistsError(workspace.name)

            # If no workspace exists with the same name, proceed with creation
            while True:
                try:
                    workspace_id = uuid4()
                    db_workspace = WorkspaceORM(
                        id=workspace_id,
                        name=workspace.name,
                        description=workspace.description,
                        created_at=datetime.now(pytz.UTC),
                        updated_at=datetime.now(pytz.UTC)
                    )
                    db_session.add(db_workspace)
                    db_session.commit()
                    db_session.refresh(db_workspace)
                    return Workspace.model_validate(db_workspace, from_attributes=True)
                except IntegrityError:
                    db_session.rollback()
                    continue  # Try again with a new UUID
        except WorkspaceAlreadyExistsError as e:
            raise e
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_workspace(workspace_id: UUID) -> Workspace:
        db_session = CortexStorage().get_session()
        try:
            db_workspace = db_session.query(WorkspaceORM).filter(
                WorkspaceORM.id == workspace_id
            ).first()
            if db_workspace is None:
                raise WorkspaceDoesNotExistError(workspace_id)
            return Workspace.model_validate(db_workspace, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_all_workspaces() -> List[Workspace]:
        db_session = CortexStorage().get_session()
        try:
            db_workspaces = db_session.query(WorkspaceORM).all()
            if not db_workspaces:
                raise NoWorkspacesExistError("No workspaces found in the database")
            return [Workspace.model_validate(workspace, from_attributes=True) for workspace in db_workspaces]
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def update_workspace(workspace: Workspace) -> Workspace:
        db_session = CortexStorage().get_session()
        try:
            db_workspace = db_session.query(WorkspaceORM).filter(
                WorkspaceORM.id == workspace.id
            ).first()
            if db_workspace is None:
                raise WorkspaceDoesNotExistError(workspace.id)

            # Update fields
            db_workspace.name = workspace.name
            db_workspace.description = workspace.description
            db_workspace.updated_at = datetime.now(pytz.UTC)

            db_session.commit()
            db_session.refresh(db_workspace)
            return Workspace.model_validate(db_workspace, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def delete_workspace(workspace: Workspace) -> bool:
        db_session = CortexStorage().get_session()
        try:
            result = db_session.query(WorkspaceORM).filter(
                WorkspaceORM.id == workspace.id
            ).delete()
            db_session.commit()
            return result > 0
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_workspace_by_name(name: str) -> Optional[Workspace]:
        db_session = CortexStorage().get_session()
        try:
            db_workspace = db_session.query(WorkspaceORM).filter(
                WorkspaceORM.name == name
            ).first()
            if db_workspace is None:
                return None
            return Workspace.model_validate(db_workspace, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()
