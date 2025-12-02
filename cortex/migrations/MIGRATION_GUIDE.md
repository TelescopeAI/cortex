# Database Migration Guide

This guide explains how to use the automatic database migration functionality in Cortex.

## Overview

Cortex now includes an automatic database migration system that can apply Alembic migrations programmatically during application startup. This eliminates the need to manually run migration commands and ensures your database is always up to date.

## Features

- **Automatic Migration Application**: Migrations are applied automatically when the application starts
- **Environment Variable Control**: Enable/disable auto-migration via `CORTEX_AUTO_APPLY_DB_MIGRATIONS`
- **Duplicate Prevention**: The `migrations_applied` flag prevents running migrations multiple times in the same session
- **Status Monitoring**: Health check endpoints provide migration status information
- **Error Handling**: Graceful error handling that doesn't prevent application startup

## Configuration

### Environment Variables

Set the following environment variable to enable automatic migrations:

```bash
export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
```

**Valid values:**
- `true`, `1`, `yes`, `on` - Enable auto-migration
- `false`, `0`, `no`, `off` (default) - Disable auto-migration

### Database Configuration

The migration system uses the same database configuration as the main application:

```bash
# PostgreSQL
export CORTEX_DB_TYPE=postgresql
export CORTEX_DB_HOST=localhost
export CORTEX_DB_PORT=5432
export CORTEX_DB_USERNAME=your_username
export CORTEX_DB_PASSWORD=your_password
export CORTEX_DB_NAME=your_database

# SQLite
export CORTEX_DB_TYPE=sqlite
export CORTEX_DB_FILE=./cortex.db

# MySQL
export CORTEX_DB_TYPE=mysql
export CORTEX_DB_HOST=localhost
export CORTEX_DB_PORT=3306
export CORTEX_DB_USERNAME=your_username
export CORTEX_DB_PASSWORD=your_password
export CORTEX_DB_NAME=your_database
```

## Usage

### Automatic Migration (Recommended)

1. Set the environment variable:
   ```bash
   export CORTEX_AUTO_APPLY_DB_MIGRATIONS=true
   ```

2. Start the application:
   ```bash
   python -m cortex.api
   ```

The application will automatically check and apply any pending migrations during startup.

### Manual Migration Control

You can also use the migration system programmatically:

```python
from cortex.core.storage.migrations import MigrationManager, auto_apply_migrations

# Option 1: Use the convenience function
success = auto_apply_migrations()

# Option 2: Use the MigrationManager directly
manager = MigrationManager()
success = manager.apply_migrations("heads")  # Apply to latest revision
```

### Checking Migration Status

The application provides health check endpoints to monitor migration status:

- **Basic Health Check**: `GET /` - Returns basic status
- **Detailed Health Check**: `GET /health` - Returns detailed status including migration information

Example response from `/health`:
```json
{
  "status": "running",
  "migration_status": {
    "current_revision": "abc123",
    "head_revision": "def456",
    "is_up_to_date": true,
    "migrations_applied": true,
    "auto_migration_enabled": true
  }
}
```

## Migration Manager API

### MigrationManager Class

The `MigrationManager` class provides the core migration functionality:

#### Methods

- `is_auto_migration_enabled()` - Check if auto-migration is enabled
- `get_current_revision()` - Get the current database revision
- `get_head_revision()` - Get the latest migration revision
- `is_database_up_to_date()` - Check if database is up to date
- `apply_migrations(target="heads")` - Apply migrations to target revision
- `auto_apply_migrations_if_enabled()` - Auto-apply if enabled
- `get_migration_status()` - Get comprehensive status information

#### Properties

- `migrations_applied` - Boolean flag indicating if migrations were applied in this session

## Error Handling

The migration system includes comprehensive error handling:

- **Database Connection Errors**: Logged but don't prevent application startup
- **Migration Failures**: Logged with detailed error information
- **Configuration Errors**: Clear error messages for missing or invalid configuration

## Testing

A test script is provided to verify the migration functionality:

```bash
python test_migrations.py
```

This script tests:
- MigrationManager creation and configuration
- Environment variable handling
- Migration status checking
- Auto-apply functionality

## Troubleshooting

### Common Issues

1. **Migrations not applying**: Check that `CORTEX_AUTO_APPLY_DB_MIGRATIONS` is set to `true`
2. **Database connection errors**: Verify your database configuration and ensure the database is running
3. **Permission errors**: Ensure the database user has sufficient privileges to create/modify tables
4. **Migration conflicts**: Check for conflicting migration files or database state
5. **Path errors**: If you see "Path doesn't exist: alembic" errors, ensure you're running the application from the project root directory

### Logs

The migration system logs all activities. Check the application logs for:
- Migration status messages
- Error details
- Database connection information

### Manual Migration

If automatic migration fails, you can still run migrations manually:

```bash
# Navigate to the migrations directory
cd migrations

# Apply migrations manually
alembic upgrade heads

# Check current status
alembic current

# Check available revisions
alembic history
```

## Best Practices

1. **Enable in Production**: Always enable auto-migration in production environments
2. **Test First**: Test migrations in development before deploying to production
3. **Backup Database**: Always backup your database before applying migrations in production
4. **Monitor Logs**: Monitor application logs for migration-related messages
5. **Health Checks**: Use the health check endpoints to monitor migration status

## Security Considerations

- The migration system uses the same database credentials as the main application
- Ensure database users have appropriate permissions (CREATE, ALTER, DROP privileges)
- Consider using read-only database users for applications that don't need migration capabilities
- Monitor migration logs for any unauthorized access attempts
