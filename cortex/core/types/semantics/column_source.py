from enum import Enum
from typing import Optional, Dict, Any
from cortex.core.types.telescope import TSModel


class ColumnSourceType(str, Enum):
    """
    Comprehensive SQL data types across all major databases.
    Represents the underlying database column type for semantic elements.
    """
    # Numeric Types
    INTEGER = "integer"
    BIGINT = "bigint"
    SMALLINT = "smallint"
    TINYINT = "tinyint"
    DECIMAL = "decimal"
    NUMERIC = "numeric"
    FLOAT = "float"
    DOUBLE = "double"
    REAL = "real"
    MONEY = "money"
    
    # String Types
    VARCHAR = "varchar"
    CHAR = "char"
    TEXT = "text"
    LONGTEXT = "longtext"
    MEDIUMTEXT = "mediumtext"
    TINYTEXT = "tinytext"
    CLOB = "clob"
    NVARCHAR = "nvarchar"
    NCHAR = "nchar"
    NTEXT = "ntext"
    
    # Temporal Types
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    TIMESTAMPTZ = "timestamptz"  # PostgreSQL timezone-aware
    TIMESTAMP_WITH_TIME_ZONE = "timestamp_with_time_zone"
    TIMESTAMP_WITHOUT_TIME_ZONE = "timestamp_without_time_zone"
    INTERVAL = "interval"
    YEAR = "year"
    
    # Boolean Types
    BOOLEAN = "boolean"
    BIT = "bit"
    
    # Binary Types
    BINARY = "binary"
    VARBINARY = "varbinary"
    BLOB = "blob"
    LONGBLOB = "longblob"
    MEDIUMBLOB = "mediumblob"
    TINYBLOB = "tinyblob"
    BYTEA = "bytea"  # PostgreSQL
    
    # JSON/Document Types
    JSON = "json"
    JSONB = "jsonb"  # PostgreSQL
    XML = "xml"
    
    # Array Types
    ARRAY = "array"
    
    # UUID/Unique Types
    UUID = "uuid"
    UNIQUEIDENTIFIER = "uniqueidentifier"  # SQL Server
    
    # Spatial/Geometry Types
    GEOMETRY = "geometry"
    GEOGRAPHY = "geography"
    POINT = "point"
    POLYGON = "polygon"
    
    # Special Types
    ENUM = "enum"
    SET = "set"
    AUTO_INCREMENT = "auto_increment"
    SERIAL = "serial"  # PostgreSQL
    IDENTITY = "identity"  # SQL Server
    
    # Unknown/Generic
    UNKNOWN = "unknown"


class ColumnSourceMeta(TSModel):
    """
    Metadata about the source column type.
    Contains type-specific information like length, precision, scale, etc.
    """
    # For VARCHAR, CHAR, NVARCHAR, etc.
    max_length: Optional[int] = None
    
    # For DECIMAL, NUMERIC, FLOAT, etc.
    precision: Optional[int] = None
    scale: Optional[int] = None
    
    # For general constraints
    nullable: Optional[bool] = None
    default_value: Optional[str] = None
    
    # For ENUM, SET types
    allowed_values: Optional[list] = None
    
    # For auto-increment, serial, identity
    is_auto_increment: Optional[bool] = None
    
    # For array types
    array_dimensions: Optional[int] = None
    element_type: Optional[str] = None
    
    # For temporal types with timezone info
    has_timezone: Optional[bool] = None
    
    # Generic metadata for any additional properties
    extra_properties: Optional[Dict[str, Any]] = None


def is_temporal_type(column_type: ColumnSourceType) -> bool:
    """Check if a column type is temporal/time-based."""
    temporal_types = {
        ColumnSourceType.DATE,
        ColumnSourceType.TIME,
        ColumnSourceType.DATETIME,
        ColumnSourceType.TIMESTAMP,
        ColumnSourceType.TIMESTAMPTZ,
        ColumnSourceType.TIMESTAMP_WITH_TIME_ZONE,
        ColumnSourceType.TIMESTAMP_WITHOUT_TIME_ZONE,
        ColumnSourceType.INTERVAL,
        ColumnSourceType.YEAR
    }
    return column_type in temporal_types


def is_numeric_type(column_type: ColumnSourceType) -> bool:
    """Check if a column type is numeric."""
    numeric_types = {
        ColumnSourceType.INTEGER,
        ColumnSourceType.BIGINT,
        ColumnSourceType.SMALLINT,
        ColumnSourceType.TINYINT,
        ColumnSourceType.DECIMAL,
        ColumnSourceType.NUMERIC,
        ColumnSourceType.FLOAT,
        ColumnSourceType.DOUBLE,
        ColumnSourceType.REAL,
        ColumnSourceType.MONEY
    }
    return column_type in numeric_types


def is_string_type(column_type: ColumnSourceType) -> bool:
    """Check if a column type is string-based."""
    string_types = {
        ColumnSourceType.VARCHAR,
        ColumnSourceType.CHAR,
        ColumnSourceType.TEXT,
        ColumnSourceType.LONGTEXT,
        ColumnSourceType.MEDIUMTEXT,
        ColumnSourceType.TINYTEXT,
        ColumnSourceType.CLOB,
        ColumnSourceType.NVARCHAR,
        ColumnSourceType.NCHAR,
        ColumnSourceType.NTEXT
    }
    return column_type in string_types
