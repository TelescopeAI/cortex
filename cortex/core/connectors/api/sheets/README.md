# Spreadsheet Data Source Configuration

This module provides support for spreadsheet-based data sources in Cortex, including CSV files and Google Sheets. It converts spreadsheets to SQLite databases for seamless integration with Cortex's semantic layer.

## Features

- File uploads via API
- Google Sheets import (token-based OAuth)
- CSV to SQLite conversion with type inference
- Multi-sheet selection
- Refresh mechanism with hash tracking
- Storage backends (local, GCS, S3)
- Encrypted file paths
- Configurable storage paths and lifecycle hooks

## Quick Start

### Environment Variables

```bash
# Storage type (local, gcs, s3)
CORTEX_SHEETS_STORAGE_TYPE=local

# Local storage paths
CORTEX_SHEETS_INPUT_STORAGE=/path/to/uploads
CORTEX_SHEETS_SQLITE_STORAGE=/path/to/databases

# File path encryption
CORTEX_FILE_STORAGE_ENCRYPTION_KEY=your-32-byte-base64-key

# GCS (if using cloud storage)
CORTEX_SHEETS_GCS_BUCKET=my-bucket
CORTEX_SHEETS_GCS_PREFIX=cortex-sheets
```

### Upload a File

```bash
curl -X POST "http://localhost:9002/api/v1/data/sources/upload?environment_id={env_id}" \
  -F "files=@data.csv"
```

Response:

```json
{
  "file_ids": ["uuid-1", "uuid-2"],
  "files": [
    {
      "id": "uuid-1",
      "name": "data",
      "extension": "csv",
      "size": 1024,
      "mime_type": "text/csv"
    }
  ]
}
```

### Create Spreadsheet Data Source

```bash
curl -X POST "http://localhost:9002/api/v1/data/sources" \
  -H "Content-Type: application/json" \
  -d '{
    "environment_id": "env-uuid",
    "name": "Sales Data",
    "source_type": "spreadsheet",
    "source_catalog": "file",
    "config": {
      "provider_type": "csv",
      "file_id": "uuid-1"
    }
  }'
```

This automatically:

- Retrieves the uploaded file
- Converts CSV to SQLite
- Infers column types
- Creates a queryable data source

## Advanced Configuration

### Custom Path Generators and Hooks

When using Cortex as a library, you can customize file storage paths and hook into lifecycle events:

```python
from cortex.core.services.data.sources.files_config import (
    FileStorageConfig,
    set_file_storage_config,
)
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

def app_upload_path(
    environment_id: UUID,
    filename: str,
    extension: str,
    source_id: str = None,
) -> str:
    return f"/data/app/environments/{environment_id}/uploads/{filename}.{extension}"

def app_sqlite_path(environment_id: UUID, source_id: str) -> str:
    return f"/data/app/environments/{environment_id}/databases/{source_id}.sqlite"

def on_upload_success(environment_id: UUID, filename: str, **context):
    file_id = context.get("file_id")
    file_size = context.get("file_size")
    logger.info("File uploaded: %s (%s bytes) to env %s", filename, file_size, environment_id)
    logger.info("File ID: %s", file_id)

def on_upload_error(environment_id: UUID, filename: str, **context):
    error = context.get("error")
    logger.error("Upload failed for %s: %s", filename, error)

def on_delete_success(environment_id: UUID, filename: str, **context):
    file_id = context.get("file_id")
    logger.info("File deleted: %s (ID: %s)", filename, file_id)

config = FileStorageConfig(
    upload_path_generator=app_upload_path,
    sqlite_path_generator=app_sqlite_path,
    on_upload_success=on_upload_success,
    on_upload_error=on_upload_error,
    on_delete_success=on_delete_success,
)
set_file_storage_config(config)
```

### Available Hooks

All hooks receive `environment_id`, `filename`, and a `**context` dict with additional data:

| Hook | When Called | Context Data |
|------|-------------|--------------|
| `on_upload_start` | Before file upload | `file_size`, `mime_type`, `hash`, `overwrite` |
| `on_upload_success` | After successful upload | `file_id`, `file_path`, `file_size` |
| `on_upload_error` | On upload error | `error`, `error_type` |
| `on_delete_start` | Before file deletion | `file_id` |
| `on_delete_success` | After successful deletion | `file_id`, `file_path` |
| `on_delete_error` | On deletion error | `error`, `file_id` |

### Path Generator Signatures

```python
def upload_path_generator(
    environment_id: UUID,
    filename: str,
    extension: str,
    source_id: Optional[str] = None,
) -> str:
    pass

def sqlite_path_generator(environment_id: UUID, source_id: str) -> str:
    pass
```

### Hook Safety

- Hooks are wrapped in try/except
- Hook errors are logged but do not break uploads or deletes
- No-op if a hook is not provided

## Type Inference

The CSV converter infers column types using these rules:

| Type | Detection Logic |
|------|----------------|
| INTEGER | >80% values are whole numbers |
| REAL | >80% values are numeric (with decimals) |
| BOOLEAN | Values are true/false, yes/no, 1/0, t/f, y/n |
| TIMESTAMP | >80% values parse as valid dates/times |
| TEXT | Default fallback |

## Storage Backends

### Local Storage (Default)

- Files in `.cortex/storage/inputs`
- SQLite DBs in `.cortex/storage/sqlite`

### Google Cloud Storage (GCS)

```bash
CORTEX_SHEETS_STORAGE_TYPE=gcs
CORTEX_SHEETS_GCS_BUCKET=my-bucket
CORTEX_SHEETS_GCS_PREFIX=cortex-sheets
```

### Amazon S3

```bash
CORTEX_SHEETS_STORAGE_TYPE=s3
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/data/sources/upload` | POST | Upload files |
| `/data/sources/files` | GET | List uploaded files |
| `/data/sources` | POST | Create spreadsheet data source |
| `/data/sources/{id}/refresh` | POST | Refresh data from source |

## Troubleshooting

### Files not appearing after upload

- Check `CORTEX_FILE_STORAGE_ENCRYPTION_KEY` is set
- Verify storage directories exist and are writable
- Check logs for encryption/decryption errors

### Custom paths not working

- Ensure `set_file_storage_config()` is called before any file operations
- Verify path generators return absolute paths
- Check directory permissions for custom paths
