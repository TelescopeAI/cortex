import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine
from cortex import migrations
from sqlalchemy import text
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

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


def _resolve_version_location() -> Path:
    """
    Resolve the correct migration version location based on database type.
    
    Priority:
    1. If CORTEX_MIGRATIONS_VERSIONS_DIRECTORY is set, use {custom_dir}/{db_type}/
    2. Otherwise use internal: {cortex_migrations}/versions/{db_type}/
    
    Returns:
        Path: The directory containing migrations for the current database type
        
    Raises:
        ValueError: If custom directory is set but doesn't exist or db_type is invalid
    """
    db_type = ExecutionEnv.get_key("CORTEX_DB_TYPE", "sqlite")
    
    # Validate db_type
    valid_types = ("sqlite", "postgresql", "mysql")
    if db_type not in valid_types:
        raise ValueError(
            f"Invalid CORTEX_DB_TYPE: '{db_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    custom_dir = ExecutionEnv.get_key("CORTEX_MIGRATIONS_VERSIONS_DIRECTORY")
    
    if custom_dir:
        # User provided custom directory
        custom_path = Path(custom_dir).resolve()
        
        if not custom_path.exists():
            raise ValueError(
                f"CORTEX_MIGRATIONS_VERSIONS_DIRECTORY points to non-existent directory: {custom_path}\n"
                f"Please ensure the directory exists with structure: {custom_path}/{db_type}/"
            )
        
        version_location = custom_path / db_type
        
        if not version_location.exists():
            raise ValueError(
                f"Database type directory does not exist: {version_location}\n"
                f"Please create the directory structure: {custom_path}/{db_type}/"
            )
    else:
        # Use internal migrations directory
        migrations_dir = _find_migrations_dir()
        version_location = migrations_dir / "alembic" / "versions" / db_type
        
        if not version_location.exists():
            raise FileNotFoundError(
                f"Internal migration directory not found: {version_location}\n"
                f"Ensure cortex migrations are properly installed."
            )
    
    logger.info(f"Using migration version location: {version_location} (db_type={db_type})")
    return version_location


class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, storage: Optional[CortexStorage] = None, interactive: bool = True):
        self.storage = storage or CortexStorage()
        self.migrations_applied = False
        self.interactive = interactive and self._is_interactive_mode()
        self.console = Console()
        self._alembic_cfg = self._get_alembic_config()
    
    def _is_interactive_mode(self) -> bool:
        """
        Determine if interactive mode should be enabled.
        
        Returns False if:
        - Not connected to a TTY (CI/CD environment)
        - CORTEX_DB_MIGRATIONS_IS_INTERACTIVE is set to false
        """
        if not sys.stdin.isatty():
            # Not a TTY, disable interactive mode for CI/CD
            logger.info("Non-TTY environment detected, disabling interactive mode")
            return False
        
        interactive_env = ExecutionEnv.get_key("CORTEX_DB_MIGRATIONS_IS_INTERACTIVE", "true")
        return str(interactive_env).lower() in ("true", "1", "yes", "on")
    
    def _has_migrations(self) -> bool:
        """Check if there are any migration scripts in the version location."""
        try:
            version_location = _resolve_version_location()
            # Count non-special files (exclude __pycache__, __init__.py, etc.)
            migration_files = [
                f for f in version_location.iterdir()
                if f.is_file() and f.suffix == '.py' and not f.name.startswith('_')
            ]
            return len(migration_files) > 0
        except Exception as e:
            logger.warning(f"Could not check if migrations exist: {e}")
            return True  # Assume migrations exist to avoid unnecessary generation
    
    def _get_alembic_config(self) -> Config:
        """Get Alembic configuration with proper database URL and database-specific version location."""
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
        
        # Resolve and set the database-specific version location
        try:
            version_location = _resolve_version_location()
            config.set_main_option('version_locations', str(version_location))
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Failed to resolve migration version location: {e}")
            raise
        
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
    
    def get_pending_migrations(self) -> List[Dict[str, str]]:
        """
        Get list of pending migrations that haven't been applied.
        
        Returns:
            List of dicts with keys: revision_id, description
        """
        try:
            script_dir = ScriptDirectory.from_config(self._alembic_cfg)
            current_rev = self.get_current_revision()
            head_rev = self.get_head_revision()
            
            if not head_rev:
                return []
            
            if not current_rev:
                # No migrations applied yet, get all
                revisions = list(script_dir.walk_revisions(head_rev, head_rev))
            else:
                # Get revisions between current and head
                revisions = list(script_dir.walk_revisions(head_rev, current_rev))
            
            pending = []
            for rev in revisions:
                if current_rev is None or rev.revision != current_rev:
                    # Get description from the revision's doc string or message
                    desc = (rev.doc or rev.message or 'No description').split('\n')[0]
                    pending.append({
                        'revision_id': rev.revision[:12],  # Short form
                        'description': desc
                    })
            
            return pending
        except Exception as e:
            logger.warning(f"Could not get pending migrations: {e}")
            return []
    
    def _display_migration_plan(self, pending_migrations: List[Dict[str, str]], operation: str = "execute") -> None:
        """Display a formatted migration plan using Rich."""
        db_type = ExecutionEnv.get_key("CORTEX_DB_TYPE", "sqlite").upper()
        current_rev = self.get_current_revision() or "None"
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Revision", style="cyan")
        table.add_column("Description")
        
        for migration in pending_migrations:
            table.add_row(migration['revision_id'], migration['description'])
        
        # Display plan
        plan_title = "MIGRATION PLAN" if operation == "execute" else "MIGRATION GENERATION PLAN"
        panel_content = f"\nDatabase Type: {db_type}\nCurrent Revision: {current_rev}\nTarget Revision: heads\n\n"
        
        self.console.print(Panel(panel_content + str(table), title=plan_title, expand=False))
        
        if operation == "execute":
            self.console.print(f"\n[yellow]{len(pending_migrations)} migration(s) will be applied[/yellow]")
            self.console.print("\n[red]⚠ Warning: This will modify your database schema[/red]")
    
    def _confirm_migration(self, operation: str = "execute") -> bool:
        """Prompt user for confirmation to proceed with migrations."""
        if not self.interactive:
            return True
        
        prompt_text = (
            "Do you want to proceed?" if operation == "execute"
            else "Do you want to generate this migration?"
        )
        
        return self.console.input(f"\n[bold]{prompt_text}[/bold] [cyan][(y)es/(n)o/(enter=yes]:[/cyan] ").lower() in ("y", "yes", "")
    
    def _fix_migration_file(self, migration_file: Path) -> None:
        """
        Post-process a generated migration file to fix imports for custom types.
        
        Alembic's autogenerate doesn't properly import custom SQLAlchemy types,
        so we manually fix them after generation.
        """
        try:
            with open(migration_file, 'r') as f:
                content = f.read()
            
            # Check if file contains references to custom types
            if 'cortex.core.types.databases' not in content:
                return
            
            # Add import statement if needed
            import_line = "from cortex.core.types.databases import JSONType, ArrayType"
            
            # Check if import already exists
            if import_line not in content and ("JSONType" in content or "ArrayType" in content):
                # Find the import section (after existing imports from alembic and sqlalchemy)
                lines = content.split('\n')
                insert_idx = 0
                
                # Find the last import line
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_idx = i + 1
                
                # Insert our import
                lines.insert(insert_idx, import_line)
                content = '\n'.join(lines)
            
            # Replace fully qualified names with short names
            content = content.replace(
                'cortex.core.types.databases.JSONType()',
                'JSONType()'
            ).replace(
                'cortex.core.types.databases.ArrayType()',
                'ArrayType()'
            )
            
            # Write back
            with open(migration_file, 'w') as f:
                f.write(content)
            
            logger.info(f"Fixed imports in migration file: {migration_file.name}")
        except Exception as e:
            logger.warning(f"Could not fix migration imports: {e}")
    
    
    def _get_next_version_number(self) -> int:
        """
        Get the next version number for auto-generated migrations.
        
        Scans existing migration files and returns the next sequential version number.
        Migration naming: <hash>_cortex_db_version_<num>_<description>.py
        
        Returns:
            int: The next version number to use
        """
        try:
            version_location = _resolve_version_location()
            existing_versions = []
            
            # Find all files containing cortex_db_version_ in the filename
            for file in version_location.iterdir():
                if file.is_file() and 'cortex_db_version_' in file.name:
                    # Extract version number from filename
                    # Format: <hash>_cortex_db_version_<num>_<description>.py
                    try:
                        # Split by 'cortex_db_version_' and get the part after it
                        parts = file.stem.split('cortex_db_version_')
                        if len(parts) > 1:
                            version_part = parts[1]  # e.g., "1_initial_migration"
                            version_num = int(version_part.split('_')[0])  # Extract just the number
                            existing_versions.append(version_num)
                    except (ValueError, IndexError):
                        continue
            
            if existing_versions:
                return max(existing_versions) + 1
            else:
                return 1
        except Exception as e:
            logger.warning(f"Could not determine next version number: {e}. Defaulting to 1")
            return 1
    
    def create_revision(
        self,
        message: str,
        autogenerate: bool = True,
        version_path: Optional[str] = None,
        skip_confirmation: bool = False
    ) -> Optional[str]:
        """
        Generate a new migration revision with interactive confirmation.
        
        Uses standardized naming convention: cortex_db_version_<num>.py
        
        Args:
            message: Description of the migration
            autogenerate: Whether to auto-detect schema changes
            version_path: Override version path (defaults to resolved DB-specific path)
            skip_confirmation: Skip interactive confirmation (for auto-generation)
            
        Returns:
            Optional[str]: The revision ID of the created migration, or None if cancelled
        """
        try:
            db_type = ExecutionEnv.get_key("CORTEX_DB_TYPE", "sqlite").upper()
            version_location = _resolve_version_location()
            
            if self.interactive and not skip_confirmation:
                # Show generation plan
                generation_info = (
                    f"\nDatabase Type: {db_type}\n"
                    f"Message: {message}\n"
                    f"Autogenerate: {'Yes' if autogenerate else 'No'}\n\n"
                    f"Target Directory:\n  {version_location}\n\n"
                    f"This will:\n"
                    f"  ✓ Analyze current database schema\n"
                    f"  ✓ Compare with SQLAlchemy models\n"
                    f"  ✓ Generate new migration script\n"
                    f"  ✓ Add to version control"
                )
                
                self.console.print(Panel(generation_info, title="MIGRATION GENERATION PLAN", expand=False))
                
                # Get confirmation
                if not self._confirm_migration("generate"):
                    self.console.print("[yellow]⚠ Generation cancelled by user[/yellow]")
                    logger.info("Migration generation cancelled by user")
                    return None
            
            # Get next version number
            version_num = self._get_next_version_number()
            # Format message with version pattern for standardized naming
            formatted_message = f"cortex_db_version_{version_num}: {message}"
            
            logger.info(f"Generating migration: {formatted_message}")
            
            # Generate the revision with standardized naming
            revision_id = command.revision(
                self._alembic_cfg,
                message=formatted_message,
                autogenerate=autogenerate,
                version_path=str(version_path or version_location)
            )
            
            # Post-process the generated migration to fix imports
            if revision_id:
                try:
                    # Extract revision ID from Script object if needed
                    rev_id = revision_id.revision if hasattr(revision_id, 'revision') else str(revision_id).split("'")[1]
                    
                    # Find the generated migration file
                    migration_files = list(version_location.glob(f"{rev_id}_*.py"))
                    if migration_files:
                        self._fix_migration_file(migration_files[0])
                except Exception as e:
                    logger.warning(f"Could not post-process migration file: {e}")
            
            if self.interactive and not skip_confirmation:
                self.console.print(f"\n[green]✓ Migration generated successfully[/green]")
                self.console.print(f"Revision ID: [cyan]{revision_id}[/cyan]")
                self.console.print(f"Version: cortex_db_version_{version_num}")
                self.console.print(f"Location: [dim]{version_location}[/dim]")
            
            logger.info(f"Migration generated successfully: {revision_id} (cortex_db_version_{version_num})")
            return revision_id
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to generate migration: {e}[/red]")
            logger.error(f"Failed to generate migration: {e}")
            return None
    
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
        Apply database migrations to the target revision with interactive confirmation.
        
        Args:
            target: Target revision to upgrade to (default: "heads")
            
        Returns:
            bool: True if migrations were applied successfully, False otherwise
        """
        if self.migrations_applied:
            logger.info("Migrations already applied in this session, skipping.")
            return True
        
        try:
            # Check if migrations exist for this database type
            auto_generated = False
            if not self._has_migrations():
                logger.info(
                    f"No migrations found for {ExecutionEnv.get_key('CORTEX_DB_TYPE', 'sqlite')}. "
                    "Auto-generating initial migration..."
                )
                
                # Auto-generate the initial migration (without interactive confirmation)
                revision_id = self.create_revision(
                    message="Initial migration - auto-generated schema",
                    autogenerate=True,
                    skip_confirmation=True  # Don't ask for confirmation on auto-generation
                )
                
                if not revision_id:
                    logger.error("Failed to auto-generate initial migration")
                    self.console.print("[red]✗ Failed to auto-generate initial migration[/red]")
                    return False
                
                logger.info(f"Auto-generated initial migration: {revision_id}")
                self.console.print(f"[green]✓ Auto-generated initial migration: {revision_id}[/green]")
                auto_generated = True
                
                # Refresh config to pick up the newly generated migration
                self._alembic_cfg = self._get_alembic_config()
            
            # Only check if up-to-date if we didn't just auto-generate
            if target == "heads" and not auto_generated and self.is_database_up_to_date():
                self.console.print("[green]✓[/green] Database is already up to date, no migrations needed.")
                self.migrations_applied = True
                return True
            
            # Get pending migrations
            pending = self.get_pending_migrations()
            
            if not pending:
                if self.interactive and not auto_generated:
                    self.console.print("[green]✓[/green] Database is up to date")
                return True
            
            # Show migration plan if interactive
            if self.interactive and pending and not auto_generated:
                self._display_migration_plan(pending, "execute")
                
                # Get confirmation
                if not self._confirm_migration("execute"):
                    self.console.print("[yellow]⚠ Migration cancelled by user[/yellow]")
                    logger.info("Migration cancelled by user")
                    return False
            elif auto_generated:
                # Auto-apply without confirmation after auto-generation
                logger.info(f"Auto-applying {len(pending)} auto-generated migration(s)...")
                if self.interactive:
                    self.console.print(f"[cyan]Applying {len(pending)} auto-generated migration(s)...[/cyan]")
            
            logger.info(f"Applying database migrations to {target}...")
            
            # Apply migrations
            command.upgrade(self._alembic_cfg, target)
            
            if self.interactive:
                self.console.print("\n[green]✓ Migration executed successfully[/green]")
                if pending:
                    self.console.print(f"\n[green]Applied {len(pending)} migration(s)[/green]")
                current_rev = self.get_current_revision()
                if current_rev:
                    self.console.print(f"Database is now at revision: [cyan]{current_rev[:12]}[/cyan]")
            
            logger.info("Database migrations applied successfully.")
            self.migrations_applied = True
            return True
            
        except Exception as e:
            self.console.print(f"[red]✗ Failed to apply migrations: {e}[/red]")
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
