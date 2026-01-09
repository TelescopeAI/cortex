# Database Migrations Guide

This guide explains the comprehensive database migration system in Cortex, designed to support multiple SQL databases (PostgreSQL, MySQL, SQLite) with maximum flexibility and safety.

## Overview

Cortex uses **Alembic** for database schema migrations with a unique multi-database approach:

- **Database-Specific Migration Chains**: Each database type (PostgreSQL, MySQL, SQLite) maintains its own separate migration chain for optimal compatibility
- **Automatic Initialization**: Missing migrations are auto-generated on first run
- **Interactive Safety System**: Confirmation required before applying migrations
- **Environment Variable Control**: Full customization via environment variables
- **Custom Migration Directories**: Support for application-specific migrations

## Architecture

### Migration Folder Structure

Migrations are organized by database type to avoid compatibility issues:

```
cortex/migrations/alembic/versions/
├── sqlite/
│   ├── a1b2c3d4e5f6_cortex_db_version_1.py
│   ├── f6e5d4c3b2a1_cortex_db_version_2.py
│   └── xyz789abc456_cortex_db_version_3.py
├── postgresql/
│   ├── 123abc456def_cortex_db_version_1.py
│   ├── 456def789abc_cortex_db_version_2.py
│   └── 789ghi012jkl_cortex_db_version_3.py
└── mysql/
    ├── pqr789stu012_cortex_db_version_1.py
    ├── stu012uvw345_cortex_db_version_2.py
    └── uvw345xyz678_cortex_db_version_3.py
```

**Why This Approach?**
- SQL dialects differ significantly between databases (especially SQLite)
- Each migration can be optimized for its specific database
- Prevents breaking changes when running the same migration across different databases
- Allows developers to have full control over database-specific SQL

## Configuration

### Environment Variables

All migration behavior is controlled through environment variables:

```bash
# Enable/disable automatic migration on startup (default: true)
export CORTEX_AUTO_APPLY_DB_MIGRATIONS="true"

# Database type (required)
# Determines which migration folder is used: sqlite/, postgresql/, or mysql/
export CORTEX_DB_TYPE="postgresql"

# Interactive confirmation before applying migrations
# (default: true when connected to TTY, false in CI/CD)
export CORTEX_DB_MIGRATIONS_IS_INTERACTIVE="true"

# Custom migration versions directory (optional)
# If not set, uses: cortex/migrations/alembic/versions/{db_type}/
# When set, must contain subdirectories for each database type: sqlite/, postgresql/, mysql/
export CORTEX_MIGRATIONS_VERSIONS_DIRECTORY="/path/to/custom/migrations"

# Custom environment file path (optional)
# If not set, loads from local.env or .env in project root
export CORTEX_ENV_FILE_PATH="/path/to/.env.custom"
```

### Database Configuration

Configure your database using standard environment variables:

```bash
# PostgreSQL
export CORTEX_DB_TYPE="postgresql"
export CORTEX_DB_HOST="localhost"
export CORTEX_DB_PORT="5432"
export CORTEX_DB_USERNAME="user"
export CORTEX_DB_PASSWORD="password"
export CORTEX_DB_NAME="cortex"

# MySQL
export CORTEX_DB_TYPE="mysql"
export CORTEX_DB_HOST="localhost"
export CORTEX_DB_PORT="3306"
export CORTEX_DB_USERNAME="user"
export CORTEX_DB_PASSWORD="password"
export CORTEX_DB_NAME="cortex"

# SQLite
export CORTEX_DB_TYPE="sqlite"
export CORTEX_DB_FILE="./cortex.db"
export CORTEX_DB_MEMORY="false"
```

## How Migrations Work

### Automatic Migrations (Recommended)

Migrations run automatically on application startup when enabled:

1. **Detect Database Type**: Reads `CORTEX_DB_TYPE` environment variable
2. **Load Migrations**: Loads migrations from the database-specific folder
3. **Generate Initial Migration**: If no migrations exist, automatically generates an initial migration
4. **Display Plan**: Shows an interactive confirmation with all pending migrations
5. **Apply Migrations**: After confirmation, applies all pending migrations

### Interactive Confirmation

When applying migrations, you'll see a Rich-formatted plan:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                   MIGRATION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Database Type: SQLITE
Current Revision: c0404f6055d9
Target Revision: heads

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Revision        ┃ Description                   ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 8bd9e9780557    │ add env_id to data models     │
│ db8068acf2bd    │ add ordering columns          │
│ 57943408a623    │ add extends column            │
└─────────────────┴───────────────────────────────┘

3 migrations will be applied

⚠ Warning: This will modify your database schema

Do you want to proceed? [y/n/enter] (y): _
```

**Response Options:**
- `y` or `yes` → Apply migrations
- `n` or `no` → Cancel
- Press `Enter` → Confirm (default is yes)

### Auto-Generation of Initial Migrations

If no migrations exist for your database type:

1. The system detects the database schema automatically
2. Generates an initial migration file following the naming convention: `cortex_db_version_1`
3. The migration is displayed for confirmation
4. After confirmation, it's applied to the database

This ensures new database types can be set up without manual intervention.

## Usage

### Automatic Migration on Startup

Enable automatic migrations in your environment:

```bash
# In your .env file or shell
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
export CORTEX_DB_TYPE=postgresql
export CORTEX_DB_HOST=localhost
export CORTEX_DB_PORT=5432
export CORTEX_DB_USERNAME=user
export CORTEX_DB_PASSWORD=password
export CORTEX_DB_NAME=cortex

# Start the API server
python -m cortex.api
```

### Manual Migration Execution

Disable automatic migrations and run manually when needed:

```bash
# In your .env file
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=false
export CORTEX_DB_TYPE=postgresql

# Start the app (no migrations run on startup)
python -m cortex.api

# In another terminal, run migrations manually when ready
cd cortex
alembic upgrade head
```

### Using the MigrationManager Programmatically

```python
from cortex.core.storage.migrations import MigrationManager

# Create a migration manager
manager = MigrationManager()

# Apply migrations with automatic type detection
success = manager.apply_migrations(target="heads")

# Check migration status
status = manager.get_migration_status()
print(f"Current revision: {status['current_revision']}")
print(f"Head revision: {status['head_revision']}")
print(f"Up to date: {status['is_up_to_date']}")

# Generate a new migration for schema changes
revision_id = manager.create_revision(
    message="add new_column to users table",
    autogenerate=True  # Auto-detect changes
)
```

### Alembic CLI Commands

You can run Alembic commands directly:

```bash
cd cortex

# Ensure database type is set
export CORTEX_DB_TYPE=sqlite

# Apply all pending migrations
alembic upgrade head

# Apply one specific migration
alembic upgrade abc123def456

# Downgrade to a specific revision
alembic downgrade def456ghi789

# View migration history
alembic history

# Get current database revision
alembic current

# Show heads of each branch
alembic branches

# Generate a new migration (autogenerate)
alembic revision --autogenerate -m "add new column"

# Generate a blank migration
alembic revision -m "custom changes"
```

**Important**: The `alembic` commands automatically detect your database type and use the correct migration folder (sqlite/, postgresql/, or mysql/).

### Using Custom Migration Directories

To use custom migrations in your application:

```bash
# Set the custom migrations directory
export CORTEX_MIGRATIONS_VERSIONS_DIRECTORY=/path/to/custom/migrations

# The directory must have this structure:
# /path/to/custom/migrations/
# ├── sqlite/
# │   ├── abc123_cortex_db_version_1.py
# │   └── def456_cortex_db_version_2.py
# ├── postgresql/
# │   ├── ghi789_cortex_db_version_1.py
# │   └── jkl012_cortex_db_version_2.py
# └── mysql/
#     ├── mno345_cortex_db_version_1.py
#     └── pqr678_cortex_db_version_2.py
```

**Important Notes:**
- The custom directory replaces the internal Cortex migrations (not combined)
- Each database type must have its own subfolder
- Custom migrations must follow the same structure and conventions

### Disabling Interactive Mode (for CI/CD)

In automated environments, disable interactive confirmation:

```bash
# In CI/CD pipeline
export CORTEX_DB_MIGRATIONS_IS_INTERACTIVE=false

# Or let the system auto-detect (false when not connected to TTY)
# This is the default for GitHub Actions, GitLab CI, etc.
```

## Migration Files Format

### Structure of a Migration File

```python
"""add environment_id to data models.

Revision ID: 8bd9e9780557
Revises: 450bd09cd019
Create Date: 2024-01-09 12:30:45.123456

"""
from alembic import op
import sqlalchemy as sa
from cortex.core.types.databases import JSONType, ArrayType

# revision identifiers, used by Alembic.
revision = '8bd9e9780557'
down_revision = '450bd09cd019'
branch_labels = None
depends_on = None

def upgrade():
    # Use op.batch_alter_table() for SQLite compatibility
    with op.batch_alter_table('data_models') as batch_op:
        batch_op.add_column(sa.Column('environment_id', sa.UUID(), nullable=True))
        batch_op.create_index('ix_data_models_environment_id', ['environment_id'])

def downgrade():
    with op.batch_alter_table('data_models') as batch_op:
        batch_op.drop_index('ix_data_models_environment_id')
        batch_op.drop_column('environment_id')
```

### Key Points:

1. **Batch Operations**: Use `op.batch_alter_table()` for SQLite compatibility
2. **Custom Types**: Import custom types like `JSONType` and `ArrayType` from `cortex.core.types.databases`
3. **Idempotent**: Migrations check for existing objects before creating/modifying them
4. **Version Naming**: Follow the convention `{hash}_cortex_db_version_{number}`

## Versioning Convention

Migration files follow a standardized naming convention:

```
{revision_hash}_cortex_db_version_{version_number}.py
```

Examples:
- `8bd9e9780557_cortex_db_version_1.py` - First migration
- `450bd09cd019_cortex_db_version_2.py` - Second migration
- `f6e5d4c3b2a1_cortex_db_version_3.py` - Third migration

Version numbers are sequential (1, 2, 3, ...) and are automatically incremented when new migrations are generated.

## Best Practices

### 1. Idempotent Migrations

Always make migrations idempotent (safe to run multiple times):

```python
def upgrade():
    # Check if table exists before creating
    inspector = sa.inspect(op.get_bind())
    if 'new_table' not in inspector.get_table_names():
        op.create_table('new_table', ...)
    
    # Check if column exists before adding
    with op.batch_alter_table('existing_table') as batch_op:
        if 'new_column' not in inspector.get_columns('existing_table'):
            batch_op.add_column(sa.Column('new_column', sa.String(255)))
```

### 2. Use Batch Operations for SQLite

SQLite has limited ALTER TABLE support, so always use batch operations:

```python
# ✅ Correct for SQLite
with op.batch_alter_table('users') as batch_op:
    batch_op.add_column(sa.Column('age', sa.Integer()))
    batch_op.alter_column('name', nullable=False)

# ❌ Won't work with SQLite
op.add_column('users', sa.Column('age', sa.Integer()))
```

### 3. Database-Specific Migrations

When a migration needs database-specific logic:

```python
# In sqlite/xxxxx_cortex_db_version_1.py
def upgrade():
    # SQLite-specific code
    op.execute("CREATE TEMPORARY TABLE users_backup AS SELECT * FROM users")
    # ... more sqlite operations

# In postgresql/xxxxx_cortex_db_version_1.py
def upgrade():
    # PostgreSQL-specific code using native features
    op.execute("CREATE EXTENSION IF NOT EXISTS uuid-ossp")
    # ... more postgresql operations
```

### 4. Testing Migrations

Always test migrations on all supported database types:

```bash
# Test on SQLite
export CORTEX_DB_TYPE=sqlite
export CORTEX_DB_FILE=./test.db
python -m cortex.api

# Test on PostgreSQL
export CORTEX_DB_TYPE=postgresql
export CORTEX_DB_HOST=localhost
# ... configure other env vars
python -m cortex.api

# Test on MySQL
export CORTEX_DB_TYPE=mysql
export CORTEX_DB_HOST=localhost
# ... configure other env vars
python -m cortex.api
```

## Troubleshooting

### Common Issues

#### 1. Migrations Not Applying

```bash
# Check if auto-migration is enabled
echo $CORTEX_AUTO_APPLY_DB_MIGRATIONS

# Check database configuration
echo $CORTEX_DB_TYPE
echo $CORTEX_DB_HOST

# Manually run migrations with verbose output
alembic upgrade head --verbose
```

#### 2. "No migrations found for database type"

```bash
# Check current database type
echo $CORTEX_DB_TYPE

# Verify migration directory structure
ls -la cortex/migrations/alembic/versions/

# Generate initial migration
cd cortex
alembic revision --autogenerate -m "initial migration"
```

#### 3. Custom Type Import Errors

```
NameError: name 'JSONType' is not defined
```

**Fix**: Ensure imports are present in migration file:

```python
from cortex.core.types.databases import JSONType, ArrayType
```

#### 4. SQLite Specific Errors

```
OperationalError: duplicate column name
```

**Fix**: Make migrations idempotent and use batch operations:

```python
def upgrade():
    with op.batch_alter_table('table_name') as batch_op:
        # Safe way to add columns
```

### Debugging

Enable debug logging to see detailed migration information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from cortex.core.storage.migrations import MigrationManager
manager = MigrationManager()
manager.apply_migrations(target="heads")
```

### Manual Recovery

If migrations fail, you can recover manually:

```bash
# Check current state
cd cortex
alembic current
alembic history

# Downgrade to a known good state
alembic downgrade <previous_revision>

# Manually review and fix database
# Then upgrade again
alembic upgrade head
```

## Performance Considerations

- **Migration Time**: Large schema changes may take time on large tables
- **Downtime**: Plan migrations during maintenance windows for production
- **Parallel Migrations**: Cortex doesn't support parallel migrations; they run sequentially
- **Testing**: Always test migration performance on production-like data volumes

## Security Considerations

- **Database Credentials**: Store in `.env` files (not in code)
- **Permissions**: Database user needs CREATE, ALTER, DROP privileges
- **Backups**: Always backup before production migrations
- **Access Control**: Limit who can modify migration files
- **Audit Logging**: Monitor migration execution in production

## Support and Documentation

For more information:
- [Installation Guide](../../cortex-docs/content/1.getting-started/3.installation.md)
- [README Database Migrations Section](../README.md#database-migrations)
- [GitHub Issues](https://github.com/TelescopeAI/cortex/issues)
