import os
import logging
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.storage.store import CortexStorage

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, storage: Optional[CortexStorage] = None):
        self.storage = storage or CortexStorage()
        self.migrations_applied = False
        self._alembic_cfg = self._get_alembic_config()
    
    def _get_alembic_config(self) -> Config:
        """Get Alembic configuration with proper database URL."""
        # Get the migrations directory path
        current_dir = Path(__file__).parent
        migrations_dir = current_dir.parent.parent.parent / "migrations"
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic configuration not found at {alembic_ini_path}")
        
        # Create Alembic config
        config = Config(str(alembic_ini_path))
        
        # Set the database URL from storage
        config.set_main_option('sqlalchemy.url', self.storage.db_url)
        
        # Set the script location to the alembic subdirectory
        config.set_main_option('script_location', str(migrations_dir / "alembic"))
        
        return config
    
    def is_auto_migration_enabled(self) -> bool:
        """Check if auto-migration is enabled via environment variable."""
        auto_migrate = ExecutionEnv.get_key("CORTEX_AUTO_APPLY_DB_MIGRATIONS", "false")
        return str(auto_migrate).lower() in ("true", "1", "yes", "on")
    
    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision."""
        try:
            engine = self.storage._sqlalchemy_engine
            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                return context.get_current_revision()
        except Exception as e:
            logger.warning(f"Could not get current revision: {e}")
            return None
    
    def get_head_revision(self) -> Optional[str]:
        """Get the head revision from migration scripts."""
        try:
            script_dir = ScriptDirectory.from_config(self._alembic_cfg)
            return script_dir.get_current_head()
        except Exception as e:
            logger.warning(f"Could not get head revision: {e}")
            return None
    
    def is_database_up_to_date(self) -> bool:
        """Check if database is up to date with migrations."""
        current_rev = self.get_current_revision()
        head_rev = self.get_head_revision()
        
        if not current_rev or not head_rev:
            return False
        
        return current_rev == head_rev
    
    def apply_migrations(self, target: str = "heads") -> bool:
        """
        Apply database migrations to the target revision.
        
        Args:
            target: Target revision to upgrade to (default: "heads")
            
        Returns:
            bool: True if migrations were applied successfully, False otherwise
        """
        if self.migrations_applied:
            logger.info("Migrations already applied in this session, skipping.")
            return True
        
        try:
            logger.info(f"Applying database migrations to {target}...")
            
            # Check if we're already up to date
            if target == "heads" and self.is_database_up_to_date():
                logger.info("Database is already up to date, no migrations needed.")
                self.migrations_applied = True
                return True
            
            # Apply migrations
            command.upgrade(self._alembic_cfg, target)
            
            logger.info("Database migrations applied successfully.")
            self.migrations_applied = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply database migrations: {e}")
            return False
    
    def auto_apply_migrations_if_enabled(self) -> bool:
        """
        Automatically apply migrations if the environment variable is enabled.
        
        Returns:
            bool: True if migrations were applied or not needed, False if failed
        """
        if not self.is_auto_migration_enabled():
            logger.info("Auto-migration is disabled (CORTEX_AUTO_APPLY_DB_MIGRATIONS not set to true)")
            return True
        
        logger.info("Auto-migration is enabled, checking database state...")
        return self.apply_migrations()
    
    def get_migration_status(self) -> dict:
        """
        Get the current migration status.
        
        Returns:
            dict: Status information including current revision, head revision, and up-to-date status
        """
        current_rev = self.get_current_revision()
        head_rev = self.get_head_revision()
        
        return {
            "current_revision": current_rev,
            "head_revision": head_rev,
            "is_up_to_date": self.is_database_up_to_date(),
            "migrations_applied": self.migrations_applied,
            "auto_migration_enabled": self.is_auto_migration_enabled()
        }


# Global migration manager instance
_migration_manager: Optional[MigrationManager] = None


def get_migration_manager() -> MigrationManager:
    """Get the global migration manager instance."""
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager


def auto_apply_migrations() -> bool:
    """
    Convenience function to auto-apply migrations using the global manager.
    
    Returns:
        bool: True if migrations were applied or not needed, False if failed
    """
    return get_migration_manager().auto_apply_migrations_if_enabled()
