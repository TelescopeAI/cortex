import os
import logging
import sys
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from cortex import migrations
from sqlalchemy import text

from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.storage.store import CortexStorage
from cortex.core.types.databases import DataSourceTypes

logger = logging.getLogger(__name__)


def _find_migrations_dir() -> Path:
    """
    Find the migrations directory.
    
    Works in both development (running from repo) and installed package scenarios.
    Since migrations is now inside the cortex package (cortex/migrations/), 
    discovery is simpler.
    """
    # Strategy 1: Import from cortex.migrations (works for both installed and dev)
    try:
        migrations_dir = Path(migrations.__file__).parent
        if (migrations_dir / "alembic.ini").exists():
            return migrations_dir
    except ImportError:
        pass
    
    # Strategy 2: Check relative to this file (fallback for development)
    # When in dev, structure is: cortex/cortex/core/storage/migrations.py
    # and cortex/cortex/migrations/
    current_dir = Path(__file__).parent
    migrations_dir = current_dir.parent.parent / "migrations"
    if (migrations_dir / "alembic.ini").exists():
        return migrations_dir
    
    raise FileNotFoundError(
        "Could not find migrations directory. "
        "Ensure the cortex package is properly installed with its migrations subpackage."
    )


class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, storage: Optional[CortexStorage] = None):
        self.storage = storage or CortexStorage()
        self.migrations_applied = False
        self._alembic_cfg = self._get_alembic_config()
    
    def _get_alembic_config(self) -> Config:
        """Get Alembic configuration with proper database URL."""
        # Get the migrations directory path
        migrations_dir = _find_migrations_dir()
        alembic_ini_path = migrations_dir / "alembic.ini"
        
        if not alembic_ini_path.exists():
            raise FileNotFoundError(f"Alembic configuration not found at {alembic_ini_path}")
        
        # Create Alembic config
        config = Config(str(alembic_ini_path))
        
        # Get database URL from storage
        db_url = self.storage.db_url
        
        # ConfigParser uses % for interpolation, so we need to escape it by doubling %%
        # This is required when URL contains URL-encoded special chars like %40 for @
        db_url_escaped = db_url.replace('%', '%%')
        
        # Log the URL (without password) for debugging
        if '@' in db_url:
            parts = db_url.split('@')
            safe_url = parts[0].split('://')[0] + '://***:***@' + '@'.join(parts[1:])
        else:
            safe_url = db_url
        logger.info(f"MigrationManager: Using database URL: {safe_url}")
        
        # Use custom config key 'tenant_db_url' instead of 'sqlalchemy.url' to avoid Alembic's sanitization
        # Alembic sanitizes 'sqlalchemy.url' which replaces passwords with ***
        config.set_main_option('tenant_db_url', db_url_escaped)
        
        # Still set sqlalchemy.url for backward compatibility, but env.py will use tenant_db_url if available
        config.set_main_option('sqlalchemy.url', db_url_escaped)
        
        # Set the script location to the alembic subdirectory
        config.set_main_option('script_location', str(migrations_dir / "alembic"))
        
        # If storage has a schema, configure Alembic to use schema-specific version table
        if hasattr(self.storage, '_env') and hasattr(self.storage._env, '_schema') and self.storage._env._schema:
            schema_name = self.storage._env._schema
            # Set version table schema so Alembic uses the tenant schema for version tracking
            config.set_main_option('version_table_schema', schema_name)
        
        return config
    
    def is_auto_migration_enabled(self) -> bool:
        """Check if auto-migration is enabled via environment variable."""
        auto_migrate = ExecutionEnv.get_key("CORTEX_AUTO_APPLY_DB_MIGRATIONS", "false")
        return str(auto_migrate).lower() in ("true", "1", "yes", "on")
    
    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision."""
        try:
            # Get version table schema if storage has a schema
            version_table_schema = None
            connect_args = {}
            
            if hasattr(self.storage, '_env') and hasattr(self.storage._env, '_schema') and self.storage._env._schema:
                version_table_schema = self.storage._env._schema
                # Set search_path in connect_args so it's applied at connection time
                # This ensures Alembic reads from the correct schema's version table
                if self.storage._env.db_type == DataSourceTypes.POSTGRESQL:
                    connect_args["options"] = f"-csearch_path={version_table_schema},public"
            
            # Always create a fresh connection to avoid caching issues
            engine = create_engine(self.storage.db_url, connect_args=connect_args)
            with engine.connect() as connection:
                context = MigrationContext.configure(
                    connection=connection,
                    opts={"version_table_schema": version_table_schema} if version_table_schema else {}
                )
                current_rev = context.get_current_revision()
            engine.dispose()  # Clean up the engine
            return current_rev
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
