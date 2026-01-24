import re
import sqlite3
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional
import duckdb
from cortex.core.utils.csv_parse import CSVParserUtil


class CortexSQLiteConverter:
    """Converts CSV data to SQLite database"""
    
    def __init__(self, db_path: str):
        """
        Initialize converter with target database path
        
        Args:
            db_path: Path where SQLite database will be created
        """
        self.db_path = db_path
        # Ensure parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def convert_from_csv_data(
        self,
        csv_data_dict: Dict[str, bytes],
        selected_tables: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Convert CSV data to SQLite tables using DuckDB

        Args:
            csv_data_dict: Dictionary mapping table names to CSV data (as bytes)
            selected_tables: List of table names to import (None = all)

        Returns:
            Dictionary mapping original names to SQLite table names
        """
        # Filter selected tables
        if selected_tables:
            csv_data_dict = {k: v for k, v in csv_data_dict.items() if k in selected_tables}

        table_mappings = {}
        tmp_dir = self._ensure_tmp_directory()

        # Create and setup DuckDB connection with SQLite extension
        duckdb_conn = self._setup_duckdb_connection()

        try:
            # Process each CSV file
            for table_name, csv_data in csv_data_dict.items():
                try:
                    safe_table_name = self._process_csv_to_sqlite(
                        duckdb_conn,
                        table_name,
                        csv_data,
                        tmp_dir
                    )
                    table_mappings[table_name] = safe_table_name
                    print(f"Created table: {safe_table_name} from {table_name}")
                except Exception as e:
                    print(f"Error parsing CSV {table_name}: {e}")
                    continue

            # Detach SQLite database
            duckdb_conn.execute("DETACH sqlite_db")

        finally:
            duckdb_conn.close()

        return table_mappings

    def _ensure_tmp_directory(self) -> Path:
        """
        Ensure .cortex/tmp directory exists and return its path

        Returns:
            Path to .cortex/tmp directory
        """
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
        tmp_dir = project_root / ".cortex" / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _setup_duckdb_connection(self):
        """
        Create DuckDB connection and setup SQLite extension

        Returns:
            DuckDB connection with SQLite extension loaded and attached
        """
        # Create in-memory DuckDB connection
        duckdb_conn = duckdb.connect(database=':memory:')

        # Load SQLite extension
        duckdb_conn.execute("INSTALL sqlite")
        duckdb_conn.execute("LOAD sqlite")

        # Attach SQLite database
        duckdb_conn.execute(f"ATTACH '{self.db_path}' AS sqlite_db (TYPE SQLITE)")

        return duckdb_conn

    def _process_csv_to_sqlite(
        self,
        duckdb_conn,
        table_name: str,
        csv_data: bytes,
        tmp_dir: Path
    ) -> str:
        """
        Process a single CSV file and write to SQLite

        Args:
            duckdb_conn: DuckDB connection
            table_name: Original table name
            csv_data: CSV data as bytes
            tmp_dir: Directory for temporary files

        Returns:
            Sanitized table name

        Raises:
            Exception: If CSV processing or SQLite writing fails
        """
        safe_table_name = self._sanitize_table_name(table_name)
        temp_csv_path = None

        try:
            # Write CSV to temporary file
            temp_csv_path = self._write_csv_to_temp_file(csv_data, tmp_dir)

            # Convert CSV to SQLite table using DuckDB
            self._create_sqlite_table_from_csv(duckdb_conn, safe_table_name, temp_csv_path)

            return safe_table_name

        finally:
            # Always clean up temp file
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)

    def _write_csv_to_temp_file(self, csv_data: bytes, tmp_dir: Path) -> str:
        """
        Write CSV bytes to a temporary file

        Args:
            csv_data: CSV data as bytes
            tmp_dir: Directory for temporary files

        Returns:
            Path to the temporary CSV file
        """
        with tempfile.NamedTemporaryFile(
            mode='wb',
            suffix='.csv',
            delete=False,
            dir=tmp_dir
        ) as temp_file:
            temp_file.write(csv_data)
            return temp_file.name

    def _create_sqlite_table_from_csv(
        self,
        duckdb_conn,
        table_name: str,
        csv_path: str
    ) -> None:
        """
        Create SQLite table from CSV file using DuckDB with explicit type inference

        Args:
            duckdb_conn: DuckDB connection with SQLite extension
            table_name: Target table name (already sanitized)
            csv_path: Path to temporary CSV file
        """
        # Infer column types using CSV parser utility
        type_inference = CSVParserUtil.infer_types(csv_path, sample_size=2)
        types_dict = type_inference.to_duckdb_types_dict()

        # Build columns parameter for DuckDB
        columns_param = ", ".join([f"'{k}': '{v}'" for k, v in types_dict.items()])

        # Drop existing table if it exists
        # Use double quotes for DuckDB identifier quoting
        duckdb_conn.execute(f'DROP TABLE IF EXISTS sqlite_db."{table_name}"')

        # Create table with explicit column types
        duckdb_conn.execute(f'''
            CREATE TABLE sqlite_db."{table_name}" AS
            SELECT * FROM read_csv('{csv_path}',
                columns = {{{columns_param}}},
                header = true
            )
        ''')

    def get_table_hash(self, table_name: str) -> str:
        """
        Compute hash of table contents for refresh detection
        
        Args:
            table_name: Name of the table (should be safe name)
            
        Returns:
            Hash of the table contents
        """
        import hashlib
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all data from table
            cursor.execute(f"SELECT * FROM [{table_name}]")
            rows = cursor.fetchall()
            conn.close()
            
            # Create hash from row data
            hasher = hashlib.sha256()
            for row in rows:
                hasher.update(str(row).encode('utf-8'))
            
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error computing hash for {table_name}: {e}")
            return ""
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database
        
        Returns:
            List of table names
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return tables
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to their SQL types
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns = cursor.fetchall()
            conn.close()
            
            schema = {}
            for col in columns:
                # col format: (cid, name, type, notnull, dflt_value, pk)
                schema[col[1]] = col[2]
            
            return schema
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return {}
    
    def _sanitize_table_name(self, name: str) -> str:
        """
        Sanitize a string to be a valid SQLite table name
        
        Args:
            name: Original name (usually filename without extension)
            
        Returns:
            Valid SQL table name
        """
        # Remove file extension if present
        if '.' in name:
            name = name.rsplit('.', 1)[0]
        
        # Replace invalid characters with underscore
        # SQLite table names can contain alphanumeric, underscore, and are case-insensitive
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "table"
        
        # Truncate if too long (SQLite has no hard limit, but keep reasonable)
        if len(sanitized) > 64:
            sanitized = sanitized[:64]
        
        return sanitized
