from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import pytz
from sqlalchemy.orm.attributes import flag_modified

from cortex.core.dashboards.dashboard import Dashboard
from cortex.core.dashboards.db.dashboard import DashboardORM
from cortex.core.exceptions.dashboards import (
    DashboardDoesNotExistError, DashboardAlreadyExistsError,
    InvalidDefaultViewError
)
from cortex.core.storage.store import CortexStorage
from cortex.core.types.telescope import TSModel


class DashboardCRUD(TSModel):
    
    @staticmethod
    def get_dashboard_by_id(dashboard_id: UUID, storage: Optional[CortexStorage] = None) -> Optional[Dashboard]:
        """
        Get dashboard by ID; views/sections/widgets are stored in dashboards.config.
        
        Args:
            dashboard_id: Dashboard ID to retrieve
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Dashboard object or None if not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_dashboard = db_session.query(DashboardORM).filter(
                DashboardORM.id == dashboard_id
            ).first()
            if db_dashboard is None:
                return None
            dashboard_dict = db_dashboard.__dict__.copy()
            config = dashboard_dict.get('config') or {}
            # Merge stored config into the response
            for key in ('views',):
                if key in config:
                    dashboard_dict[key] = config[key]
            # default_view may be string alias or UUID stored as string
            return Dashboard.model_validate(dashboard_dict, from_attributes=True)
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def get_dashboards_by_environment(environment_id: UUID, storage: Optional[CortexStorage] = None) -> List[Dashboard]:
        """
        Get all dashboards for an environment.
        
        Args:
            environment_id: Environment ID to get dashboards for
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            List of dashboard objects
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_dashboards = db_session.query(DashboardORM).filter(
                DashboardORM.environment_id == environment_id
            ).all()
            
            dashboards = []
            for db_dashboard in db_dashboards:
                dashboard_dict = db_dashboard.__dict__.copy()
                config = dashboard_dict.get('config') or {}
                if 'views' in config:
                    dashboard_dict['views'] = config['views']
                dashboards.append(Dashboard.model_validate(dashboard_dict, from_attributes=True))
            
            return dashboards
        except Exception as e:
            raise e
        finally:
            db_session.close()

    @staticmethod
    def add_dashboard(dashboard: Dashboard, storage: Optional[CortexStorage] = None) -> Dashboard:
        """
        Create a new dashboard. Stores nested structures in dashboards.config.
        
        Args:
            dashboard: Dashboard object to create
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Created dashboard object
            
        Raises:
            DashboardAlreadyExistsError: If dashboard with same name exists in environment
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Check if dashboard with same name exists in environment
            existing = db_session.query(DashboardORM).filter(
                DashboardORM.name == dashboard.name,
                DashboardORM.environment_id == dashboard.environment_id
            ).first()
            if existing:
                raise DashboardAlreadyExistsError(dashboard.name, dashboard.environment_id)

            dashboard_id = dashboard.id or uuid4()
            db_dashboard = DashboardORM(
                id=dashboard_id,
                environment_id=dashboard.environment_id,
                name=dashboard.name,
                description=dashboard.description,
                type=dashboard.type.value,
                default_view=str(dashboard.default_view),
                tags=dashboard.tags,
                created_by=dashboard.created_by,
                created_at=datetime.now(pytz.UTC),
                updated_at=datetime.now(pytz.UTC),
                last_viewed_at=dashboard.last_viewed_at,
                config={
                    'alias': dashboard.alias,
                    'views': [v.model_dump() for v in dashboard.views],
                }
            )
            
            db_session.add(db_dashboard)
            db_session.commit()
            db_session.refresh(db_dashboard)
            
            dashboard_dict = db_dashboard.__dict__.copy()
            config = dashboard_dict.get('config') or {}
            if 'views' in config:
                dashboard_dict['views'] = config['views']
            
            return Dashboard.model_validate(dashboard_dict, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def update_dashboard(dashboard_id: UUID, dashboard: Dashboard, storage: Optional[CortexStorage] = None) -> Dashboard:
        """
        Update an existing dashboard and its JSON config.
        
        Args:
            dashboard_id: Dashboard ID to update
            dashboard: Updated dashboard object
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Updated dashboard object
            
        Raises:
            DashboardDoesNotExistError: If dashboard not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_dashboard = db_session.query(DashboardORM).filter(
                DashboardORM.id == dashboard_id
            ).first()
            if db_dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)

            # Update dashboard fields
            db_dashboard.name = dashboard.name
            db_dashboard.description = dashboard.description
            db_dashboard.type = dashboard.type.value
            db_dashboard.default_view = str(dashboard.default_view)
            db_dashboard.tags = dashboard.tags
            db_dashboard.updated_at = datetime.now(pytz.UTC)
            if dashboard.last_viewed_at:
                db_dashboard.last_viewed_at = dashboard.last_viewed_at
            # Update config (alias and views)
            config = db_dashboard.config or {}
            config['alias'] = dashboard.alias
            # Accept updates even if caller provided raw dicts
            if hasattr(dashboard, 'views') and dashboard.views is not None:
                try:
                    config['views'] = [
                        v if isinstance(v, dict) else v.model_dump()  # type: ignore
                        for v in dashboard.views  # type: ignore
                    ]
                except Exception:
                    # Fallback to previous config views if serialization fails
                    config['views'] = config.get('views', [])
            # Assign a new dict and explicitly flag as modified so SQLAlchemy persists JSON changes
            db_dashboard.config = dict(config)
            flag_modified(db_dashboard, 'config')

            db_session.commit()
            db_session.refresh(db_dashboard)
            
            dashboard_dict = db_dashboard.__dict__.copy()
            config = dashboard_dict.get('config') or {}
            if 'views' in config:
                dashboard_dict['views'] = config['views']
            
            return Dashboard.model_validate(dashboard_dict, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def delete_dashboard(dashboard_id: UUID, storage: Optional[CortexStorage] = None) -> bool:
        """
        Delete a dashboard and all its related data.
        
        Args:
            dashboard_id: Dashboard ID to delete
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            True if dashboard was deleted successfully
            
        Raises:
            DashboardDoesNotExistError: If dashboard not found
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            db_dashboard = db_session.query(DashboardORM).filter(
                DashboardORM.id == dashboard_id
            ).first()
            if db_dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)

            # Delete all related data (cascade should handle this)
            db_session.delete(db_dashboard)
            db_session.commit()
            return True
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    @staticmethod
    def set_default_view(dashboard_id: UUID, view_id: UUID, storage: Optional[CortexStorage] = None) -> Dashboard:
        """
        Set the default view for a dashboard.
        
        Args:
            dashboard_id: Dashboard ID to set default view for
            view_id: View ID or alias to set as default
            storage: Optional CortexStorage instance. If not provided, uses singleton.
            
        Returns:
            Updated dashboard object
            
        Raises:
            DashboardDoesNotExistError: If dashboard not found
            InvalidDefaultViewError: If view_id is not valid
        """
        db_session = (storage or CortexStorage()).get_session()
        try:
            # Verify dashboard exists
            db_dashboard = db_session.query(DashboardORM).filter(
                DashboardORM.id == dashboard_id
            ).first()
            if db_dashboard is None:
                raise DashboardDoesNotExistError(dashboard_id)

            # Accept UUID or alias; check within JSON config
            config = db_dashboard.config or {}
            view_aliases = {v.get('alias'): v.get('id') for v in config.get('views', []) if isinstance(v, dict)}
            # If provided view_id does not match any UUIDs, consider alias lookup
            valid_ids = {str(v.get('id')) for v in config.get('views', [])}
            candidate = str(view_id)
            if candidate not in valid_ids:
                # try alias mapping
                candidate = str(view_aliases.get(str(view_id))) if view_aliases.get(str(view_id)) else candidate
            if candidate not in valid_ids:
                raise InvalidDefaultViewError(dashboard_id, view_id)

            # Update default view
            db_dashboard.default_view = candidate
            db_dashboard.updated_at = datetime.now(pytz.UTC)
            
            db_session.commit()
            db_session.refresh(db_dashboard)
            
            dashboard_dict = db_dashboard.__dict__.copy()
            config = dashboard_dict.get('config') or {}
            if 'views' in config:
                dashboard_dict['views'] = config['views']
            
            return Dashboard.model_validate(dashboard_dict, from_attributes=True)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    # Legacy view/section/widget CRUD removed due to single-table config design