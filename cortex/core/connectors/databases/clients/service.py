from cortex.core.connectors.databases.clients.SQL.common import (
    CommonProtocolSQLClient,
    DuckDBClient,
    SQLiteClient,
)
from cortex.core.connectors.databases.clients.factory.implementations import (
    BigQueryClientFactory,
    CommonProtocolSQLClientFactory,
    DuckDBClientFactory,
    SQLiteClientFactory,
)
from cortex.core.connectors.databases.clients.generator import DatabaseClientGenerator
from cortex.core.connectors.databases.credentials.SQL.bigquery import BigQueryCredentialsFactory
from cortex.core.connectors.databases.credentials.SQL.common import (
    CommonProtocolSQLCredentialsFactory,
    DuckDBCredentialsFactory,
    SQLiteCredentialsFactory,
)
from cortex.core.connectors.databases.credentials.generator import DatabaseCredentialsGenerator
from cortex.core.types.databases import DataSourceTypes
from cortex.core.types.telescope import TSModel


class DBClientService(TSModel):

    @staticmethod
    def _resolve_gcs_path(file_path: str) -> str:
        """Resolve GCS paths to local cache paths"""
        if not file_path or not file_path.startswith('gs://'):
            return file_path
        
        # GCS path detected - resolve to local cache
        from cortex.core.connectors.api.sheets.cache import CortexFileStorageCacheManager
        from cortex.core.connectors.api.sheets.config import get_sheets_config
        from cortex.core.connectors.api.sheets.storage.gcs import CortexFileStorageGCSBackend
        
        sheets_config = get_sheets_config()
        cache_manager = CortexFileStorageCacheManager(
            cache_dir=sheets_config.cache_dir,
            sqlite_dir=sheets_config.sqlite_storage_path,
            max_size_gb=sheets_config.cache_max_size_gb
        )
        gcs_backend = CortexFileStorageGCSBackend(
            bucket_name=sheets_config.gcs_bucket,
            prefix=sheets_config.gcs_prefix,
            cache_manager=cache_manager
        )
        
        # Extract blob path from gs:// URI
        # Format: gs://bucket/prefix/sqlite/source_id.db
        blob_path = file_path.replace(f"gs://{sheets_config.gcs_bucket}/", "")
        
        # Extract source_id from blob path for cache manager
        # blob_path format: prefix/sqlite/source_id.db
        parts = blob_path.split('/')
        source_id = parts[-1].replace('.db', '') if parts else 'default'
        
        # Get local cached path (downloads if not cached)
        local_path = cache_manager.get_cached_path(
            file_id=source_id,
            remote_path=blob_path,
            storage_backend=gcs_backend
        )
        
        return local_path

    @staticmethod
    def get_client(details: dict, db_type: DataSourceTypes):
        factory = None
        client = None
        creds = None
        if db_type in {DataSourceTypes.POSTGRESQL, DataSourceTypes.MYSQL}:
            creds_factory = CommonProtocolSQLCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = CommonProtocolSQLClientFactory()
        elif db_type in {DataSourceTypes.SQLITE, DataSourceTypes.SPREADSHEET}:
            # SPREADSHEET type uses SQLite backend
            # Resolve GCS paths to local cache before creating credentials
            # Check sqlite_path first (canonical location), then file_path
            sqlite_path = details.get('sqlite_path') or details.get('file_path')
            if sqlite_path:
                resolved_path = DBClientService._resolve_gcs_path(sqlite_path)
                # Update file_path with resolved local path for credentials
                details['file_path'] = resolved_path
            
            creds_factory = SQLiteCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = SQLiteClientFactory()
        elif db_type == DataSourceTypes.DUCKDB:
            creds_factory = DuckDBCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = DuckDBClientFactory()
        elif db_type == DataSourceTypes.BIGQUERY:
            creds_factory = BigQueryCredentialsFactory()
            creds = DatabaseCredentialsGenerator().parse(factory=creds_factory, **details)
            client_factory = BigQueryClientFactory()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        client = DatabaseClientGenerator().parse(factory=client_factory, credentials=creds)
        return client

