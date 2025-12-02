import sys
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from sqlalchemy import MetaData
from sqlalchemy.engine import make_url
from cortex.core.storage.store import CortexStorage

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

    """
    # Use the SAME engine as the application to ensure consistency
    storage = CortexStorage()
    
    # Use the application's engine instead of creating a new one
    connectable = storage._sqlalchemy_engine
    # print("DB URL: ", db_uri)

    with connectable.connect() as connection:
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            render_as_batch=is_sqlite,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
