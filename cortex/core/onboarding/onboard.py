# Onboarding Operations
import logging
from typing import List, Optional
from uuid import UUID

from cortex.core.data.db.model_service import DataModelService
from cortex.core.data.modelling.model import DataModel
from cortex.core.exceptions.environments import NoEnvironmentsExistError
from cortex.core.exceptions.workspaces import NoWorkspacesExistError
from cortex.core.storage.migrations import auto_apply_migrations
from cortex.core.types.telescope import TSModel
from cortex.core.workspaces.db.environment_service import EnvironmentCRUD
from cortex.core.workspaces.db.workspace_service import WorkspaceCRUD
from cortex.core.workspaces.environments.environment import WorkspaceEnvironment
from cortex.core.workspaces.workspace import Workspace


class OnboardingManager(TSModel):
    """Manages all onboarding operations for the Cortex application."""
    
    def run(self) -> bool:
        """
        Execute all onboarding operations.
        
        All operations will be executed regardless of whether previous ones succeeded or failed.
        
        Returns:
            bool: True if all onboarding operations completed successfully, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        # Track success of each operation
        migrations_success = False
        workspace_env_success = False
        data_model_success = False
        
        # Apply database migrations
        migrations_success = self._apply_migrations()
        
        # Ensure default workspace and environment exist
        workspace_env_success = self._ensure_default_workspace_and_environment()
        
        # Create default data model if none exists
        data_model_success = self._ensure_default_data_model()
        
        # Return True only if all operations succeeded
        if migrations_success and workspace_env_success and data_model_success:
            logger.info("All onboarding operations completed successfully.")
            return True
        else:
            failed_operations = []
            if not migrations_success:
                failed_operations.append("migrations")
            if not workspace_env_success:
                failed_operations.append("workspace/environment initialization")
            if not data_model_success:
                failed_operations.append("default data model creation")
            logger.warning(f"Some onboarding operations failed: {', '.join(failed_operations)}")
            return False
    
    def _apply_migrations(self) -> bool:
        """
        Apply database migrations if auto-migration is enabled.
        
        Returns:
            bool: True if migrations were applied successfully or not needed, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        try:
            success = auto_apply_migrations()
            if success:
                logger.info("Database migration check completed successfully.")
                return True
            else:
                logger.error("Database migration failed. Please check your database configuration.")
                # Note: We don't exit here to allow the application to start for debugging
                return False
        except Exception as e:
            logger.error(f"Error during database migration: {e}")
            # Note: We don't exit here to allow the application to start for debugging
            return False
    
    def _ensure_default_workspace_and_environment(self) -> bool:
        """
        Ensure that at least one workspace exists, and if there's exactly one workspace,
        ensure it has at least one environment.
        
        - If no workspaces exist: Create a "Default" workspace and a "Test" environment within it.
        - If exactly 1 workspace exists and no environments: Create a "Test" environment within that workspace.
        
        Returns:
            bool: True if operation completed successfully, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Check if any workspaces exist
            workspaces = self._get_all_workspaces()
            
            if len(workspaces) == 0:
                # No workspaces exist - create Default workspace and Test environment
                logger.info("No workspaces found. Creating default workspace and test environment...")
                default_workspace = self._create_default_workspace()
                if default_workspace:
                    self._create_test_environment(default_workspace.id)
                    logger.info("Default workspace and Test environment created successfully.")
                    return True
                else:
                    logger.error("Failed to create default workspace.")
                    return False
            
            elif len(workspaces) == 1:
                # Exactly one workspace exists - check if it has environments
                workspace = workspaces[0]
                environments = self._get_environments_for_workspace(workspace.id)
                
                if len(environments) == 0:
                    # No environments exist - create Test environment
                    logger.info(f"No environments found for workspace '{workspace.name}'. Creating Test environment...")
                    self._create_test_environment(workspace.id)
                    logger.info("Test environment created successfully.")
                    return True
                else:
                    logger.info(f"Workspace '{workspace.name}' already has {len(environments)} environment(s).")
                    return True
            
            else:
                # Multiple workspaces exist - nothing to do
                logger.info(f"Found {len(workspaces)} workspaces. Skipping default workspace/environment creation.")
                return True
                
        except Exception as e:
            logger.error(f"Error during workspace/environment initialization: {e}")
            # Note: We don't exit here to allow the application to start for debugging
            return False
    
    def _get_all_workspaces(self) -> List[Workspace]:
        """
        Get all workspaces from the database.
        
        Returns:
            List[Workspace]: List of workspaces, empty list if none exist
        """
        try:
            return WorkspaceCRUD.get_all_workspaces()
        except NoWorkspacesExistError:
            return []
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving workspaces: {e}")
            return []
    
    def _get_environments_for_workspace(self, workspace_id: UUID) -> List[WorkspaceEnvironment]:
        """
        Get all environments for a given workspace.
        
        Args:
            workspace_id: UUID of the workspace
            
        Returns:
            List[WorkspaceEnvironment]: List of environments, empty list if none exist
        """
        try:
            return EnvironmentCRUD.get_environments_by_workspace(workspace_id)
        except NoEnvironmentsExistError:
            return []
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error retrieving environments for workspace {workspace_id}: {e}")
            return []
    
    def _create_default_workspace(self) -> Optional[Workspace]:
        """
        Create a default workspace named "Default".
        
        Returns:
            Optional[Workspace]: The created workspace, or None if creation failed
        """
        logger = logging.getLogger(__name__)
        
        try:
            workspace = Workspace(
                name="Default",
                description="Default workspace created during onboarding"
            )
            created_workspace = WorkspaceCRUD.add_workspace(workspace)
            logger.info(f"Created default workspace: {created_workspace.name} (ID: {created_workspace.id})")
            return created_workspace
        except Exception as e:
            logger.error(f"Error creating default workspace: {e}")
            return None
    
    def _create_test_environment(self, workspace_id: UUID) -> Optional[WorkspaceEnvironment]:
        """
        Create a test environment named "Test" within the specified workspace.
        
        Args:
            workspace_id: UUID of the workspace to create the environment in
            
        Returns:
            Optional[WorkspaceEnvironment]: The created environment, or None if creation failed
        """
        logger = logging.getLogger(__name__)
        
        try:
            environment = WorkspaceEnvironment(
                workspace_id=workspace_id,
                name="Test",
                description="Test environment created during onboarding"
            )
            created_environment = EnvironmentCRUD.add_environment(environment)
            logger.info(f"Created test environment: {created_environment.name} (ID: {created_environment.id}) in workspace {workspace_id}")
            return created_environment
        except Exception as e:
            logger.error(f"Error creating test environment: {e}")
            return None
    
    def _ensure_default_data_model(self) -> bool:
        """
        Ensure that at least one data model exists.
        
        - If no data models exist: Create a "Default Data Model" in the first available environment.
        
        Returns:
            bool: True if operation completed successfully, False otherwise
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Get all workspaces and environments
            workspaces = self._get_all_workspaces()
            
            if len(workspaces) == 0:
                # No workspaces exist, skip data model creation
                logger.info("No workspaces found. Skipping default data model creation.")
                return True
            
            # Get the first environment from the first workspace
            first_workspace = workspaces[0]
            environments = self._get_environments_for_workspace(first_workspace.id)
            
            if len(environments) == 0:
                # No environments exist, skip data model creation
                logger.info("No environments found. Skipping default data model creation.")
                return True
            
            first_environment = environments[0]
            
            # Check if any data models already exist in this environment
            model_service = DataModelService()
            existing_models = model_service.get_all_data_models(
                environment_id=first_environment.id,
                skip=0,
                limit=1
            )
            
            if len(existing_models) > 0:
                logger.info(f"Data model(s) already exist in environment '{first_environment.name}'. Skipping default data model creation.")
                return True
            
            # Create default data model
            logger.info(f"No data models found. Creating default data model in environment '{first_environment.name}'...")
            default_model = DataModel(
                environment_id=first_environment.id,
                name="Default Data Model",
                description="Default data model created during onboarding"
            )
            
            created_model = model_service.create_data_model(default_model)
            model_service.close()
            
            logger.info(f"Created default data model: {created_model.name} (ID: {created_model.id}) in environment {first_environment.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error during default data model creation: {e}")
            return False
