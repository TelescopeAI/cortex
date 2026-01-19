import io
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


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
        Convert CSV data to SQLite tables
        
        Args:
            csv_data_dict: Dictionary mapping table names to CSV data (as bytes)
            selected_tables: List of table names to import (None = all)
            
        Returns:
            Dictionary mapping original names to SQLite table names
        """
        # If selected tables specified, filter the data
        if selected_tables:
            csv_data_dict = {k: v for k, v in csv_data_dict.items() if k in selected_tables}
        
        table_mappings = {}
        
        # Create or connect to SQLite database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for table_name, csv_data in csv_data_dict.items():
                # Convert table name to valid SQL identifier
                safe_table_name = self._sanitize_table_name(table_name)
                
                # Parse CSV data
                try:
                    df = pd.read_csv(io.BytesIO(csv_data))
                except Exception as e:
                    print(f"Error parsing CSV {table_name}: {e}")
                    continue
                
                # Infer column types from data
                df = self._infer_and_cast_types(df)
                
                # Drop existing table if it exists (for refresh operations)
                cursor.execute(f"DROP TABLE IF EXISTS [{safe_table_name}]")
                
                # Create table from DataFrame
                df.to_sql(safe_table_name, conn, if_exists='replace', index=False)
                
                table_mappings[table_name] = safe_table_name
                print(f"Created table: {safe_table_name} from {table_name}")
            
            conn.commit()
        finally:
            conn.close()
        
        return table_mappings
    
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
    
    def _infer_and_cast_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Infer and cast column types for better SQLite storage
        Handles: INTEGER, REAL, BOOLEAN, TEXT, TIMESTAMP
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with inferred types
        """
        for col in df.columns:
            try:
                # Skip if column has all NaN values
                if df[col].isna().all():
                    continue
                
                # Skip if not object type (already typed)
                if df[col].dtype != 'object':
                    continue
                
                # Get non-null values to analyze
                non_null_values = df[col].dropna()
                if len(non_null_values) == 0:
                    continue
                
                # Try numeric conversion first
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                numeric_ratio = numeric_col.notna().sum() / len(df)
                
                if numeric_ratio > 0.8:  # >80% numeric
                    # Check if all numeric values are integers
                    numeric_non_null = numeric_col.dropna()
                    if (numeric_non_null == numeric_non_null.astype(int)).all():
                        df[col] = numeric_col.astype('Int64')  # Nullable integer
                    else:
                        df[col] = numeric_col.astype('float64')
                    continue
                
                # Try boolean conversion
                if self._is_boolean(non_null_values):
                    df[col] = df[col].map(lambda x: self._to_bool(x) if pd.notna(x) else None)
                    continue
                
                # Try datetime conversion
                datetime_col = pd.to_datetime(df[col], errors='coerce')
                datetime_ratio = datetime_col.notna().sum() / len(df)
                
                if datetime_ratio > 0.8:  # >80% are valid dates
                    df[col] = datetime_col
                    continue
                
                # Default: keep as string/TEXT (no conversion needed)
                # pandas will store as object type, SQLite will map to TEXT
                
            except Exception as e:
                print(f"Error inferring type for column {col}: {e}")
                continue
        
        return df
    
    def _is_boolean(self, series: pd.Series) -> bool:
        """
        Check if a series contains boolean-like values
        
        Args:
            series: Pandas series to check
            
        Returns:
            True if series is boolean-like
        """
        bool_values = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        unique_lower = set(str(v).strip().lower() for v in series.unique() if pd.notna(v))
        return unique_lower.issubset(bool_values) and len(unique_lower) <= 2
    
    def _to_bool(self, val) -> Optional[bool]:
        """
        Convert a value to boolean
        
        Args:
            val: Value to convert
            
        Returns:
            Boolean value or None
        """
        if pd.isna(val):
            return None
        str_val = str(val).strip().lower()
        return str_val in {'true', 'yes', '1', 't', 'y'}
