import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from sqlalchemy import MetaData
from sqlalchemy.engine import make_url
from cortex.core.storage.store import CortexStorage
from sqlalchemy import create_engine as create_engine_from_url, text
from sqlalchemy.pool import NullPool
from cortex.core.storage.store import _tenant_storage
sys.path = ['', '..'] + sys.path[1:]



# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)
target_metadata = CortexStorage().Base.metadata

count = 0
for table in target_metadata.tables.values():
    print("Table: ", table)
    count += 1
print("Total Tables: ", count)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
# Resolve DB URI and normalize file-based paths for SQLite/DuckDB to project root


raw_uri = CortexStorage().db_url
try:
    parsed = make_url(raw_uri)
    driver = parsed.drivername or ""
    is_sqlite = "sqlite" in driver
    if "duckdb" in driver:
        raise RuntimeError("DuckDB migrations are temporarily unsupported in env.py. Use SQLite/Postgres/MySQL.")
    if is_sqlite and parsed.database and parsed.database != ":memory:":
        db_path = Path(parsed.database)
        if not db_path.is_absolute():
            # Path is: cortex/cortex/migrations/alembic/env.py
            # parents[3] gets us to the project root (cortex/)
            project_root = Path(__file__).resolve().parents[3]
            abs_path = (project_root / db_path).resolve()
            parsed = parsed.set(database=abs_path.as_posix())
    db_uri = str(parsed).replace('%', '%%')
except Exception:
    db_uri = raw_uri.replace('%', '%%')
config.set_main_option('sqlalchemy.url', r"{}".format(db_uri))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = url is not None and url.startswith("sqlite")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=is_sqlite,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    Supports both:
    1. Default mode: Uses singleton CortexStorage()
    2. Tenant mode: Uses custom storage via MigrationManager (with schema isolation)
    """
    
    
    # Get the database URL from custom config key to avoid Alembic's sanitization
    # Alembic sanitizes 'sqlalchemy.url' which replaces passwords with ***
    # Use 'tenant_db_url' if set (by MigrationManager), otherwise fall back to 'sqlalchemy.url'
    db_url_config = config.get_main_option('tenant_db_url', None)
    if not db_url_config:
        # Fallback to sqlalchemy.url for backward compatibility
        db_url_config = config.get_main_option('sqlalchemy.url')
    
    # Log the URL being used (without password) for debugging
    if db_url_config and '@' in db_url_config:
        safe_url = db_url_config.split('@')[0].split('://')[0] + '://***:***@' + '@'.join(db_url_config.split('@')[1:])
    else:
        safe_url = db_url_config or "NOT SET"
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Alembic env.py: Using database URL: {safe_url}")
    
    if not db_url_config or db_url_config == "driver://user:pass@localhost/dbname":
        raise ValueError(
            "Database URL not properly configured. "
            "Ensure MigrationManager is setting tenant_db_url correctly."
        )
    
    # Create engine from the configured URL
    # This handles both default and tenant-specific schemas
    connectable = create_engine_from_url(db_url_config, poolclass=NullPool)
    try:
        with connectable.connect() as connection:
            is_sqlite = connection.dialect.name == "sqlite"

            # Get version table schema from config if set (for tenant schemas)
            version_table_schema = config.get_main_option('version_table_schema', None)

            # For PostgreSQL with tenant schema, ensure search_path is set
            if connection.dialect.name == "postgresql" and version_table_schema:
                # Use schema from config (set by MigrationManager)
                connection.execute(text(f"SET search_path TO {version_table_schema}, public"))
                connection.commit()
            elif connection.dialect.name == "postgresql":
                # Fallback: try to get from tenant context if available
                try:
                    tenant_storage = _tenant_storage.get()
                    if tenant_storage and hasattr(tenant_storage, '_env') and hasattr(tenant_storage._env,
                                                                                      '_schema') and tenant_storage._env._schema:
                        schema_name = tenant_storage._env._schema
                        connection.execute(text(f"SET search_path TO {schema_name}, public"))
                        version_table_schema = schema_name  # Use for version table too
                except Exception:
                    pass  # If we can't set schema, migrations will use default/public schema

            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                include_schemas=True,
                include_name=version_table_schema,
                compare_type=True,
                render_as_batch=is_sqlite,
                version_table_schema=version_table_schema if version_table_schema else None,
            )

            with context.begin_transaction():
                context.run_migrations()

    except Exception as e:
        print(f"Failed to run migrations: {e}")

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
