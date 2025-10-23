from typing import Optional, Dict, List
from cortex.core.types.sql_schema import DatabaseSchema, TableSchema, ColumnSchema
from cortex.core.types.semantics.column_source import ColumnSourceType, ColumnSourceMeta
from cortex.core.semantics.measures import SemanticMeasure
from cortex.core.semantics.dimensions import SemanticDimension
from cortex.core.semantics.filters import SemanticFilter


def get_qualified_column_name(column_query: str, 
                            table_name: Optional[str] = None,
                            table_prefix: Optional[str] = None,
                            has_joins: bool = False,
                            quote_identifiers: bool = False) -> str:
    """
    Get a fully qualified column name with table prefix when joins are present.
    Automatically wraps column names containing spaces or special characters in quotes.
    
    Args:
        column_query: The column name or expression
        table_name: The table name for the column
        table_prefix: Optional table prefix to use instead of table_name
        has_joins: Whether joins are present (affects qualification logic)
        quote_identifiers: If True, always quote column identifiers (PostgreSQL style)
        
    Returns:
        Qualified column name with proper quoting
    """
    # Helper function to wrap column names in quotes when needed
    def _quote_if_needed(column: str) -> str:
        column = column.strip()
        # Already quoted, return as-is
        if column.startswith('"') and column.endswith('"'):
            return column
        # Always quote if quote_identifiers is True (PostgreSQL style)
        if quote_identifiers:
            return f'"{column}"'
        # Otherwise, only quote if column contains spaces or special characters
        if ' ' in column:
            return f'"{column}"'
        return column
    
    # Determine the prefix to use
    prefix = table_prefix or table_name
    
    # If no joins are present and no prefix needed, return column as-is (but quote if needed)
    if not has_joins and not prefix:
        return _quote_if_needed(column_query)
    
    # If column already contains a table prefix (has a dot), handle it
    if '.' in column_query:
        if prefix:
            # Replace the existing table prefix with the new one
            column_part = column_query.split('.', 1)[1]  # Get everything after the first dot
            quoted_column = _quote_if_needed(column_part)
            return f"{prefix}.{quoted_column}"
        else:
            # No new prefix provided, but still quote the column part
            parts = column_query.split('.', 1)
            table_part = parts[0]
            column_part = parts[1]
            quoted_column = _quote_if_needed(column_part)
            return f"{table_part}.{quoted_column}"
    else:
        # Column doesn't have a table prefix
        if prefix:
            quoted_column = _quote_if_needed(column_query)
            return f"{prefix}.{quoted_column}"
        return _quote_if_needed(column_query)


def map_database_type_to_source_type(db_type: str) -> ColumnSourceType:
    """
    Map database-specific type names to our standardized ColumnSourceType enum.
    Handles variations across different SQL databases.
    """
    # Normalize the type name - remove extra spaces and parentheses
    db_type_upper = db_type.upper().strip().split('(')[0].strip()
    
    # Debug logging (can be removed in production)
    # print(f"Mapping database type: '{db_type}' -> '{db_type_upper}'")
    
    # Integer types
    if db_type_upper in ['INTEGER', 'INT', 'INT4', 'SERIAL']:
        return ColumnSourceType.INTEGER
    elif db_type_upper in ['BIGINT', 'INT8', 'BIGSERIAL']:
        return ColumnSourceType.BIGINT
    elif db_type_upper in ['SMALLINT', 'INT2', 'SMALLSERIAL']:
        return ColumnSourceType.SMALLINT
    elif db_type_upper in ['TINYINT']:
        return ColumnSourceType.TINYINT
    
    # Decimal/Float types
    elif db_type_upper in ['DECIMAL', 'DEC', 'NUMERIC']:
        return ColumnSourceType.DECIMAL
    elif db_type_upper in ['FLOAT', 'FLOAT4', 'REAL']:
        return ColumnSourceType.FLOAT
    elif db_type_upper in ['DOUBLE', 'FLOAT8', 'DOUBLE_PRECISION', 'DOUBLE PRECISION']:
        return ColumnSourceType.DOUBLE
    elif db_type_upper in ['MONEY']:
        return ColumnSourceType.MONEY
    
    # String types
    elif db_type_upper in ['VARCHAR', 'CHARACTER_VARYING']:
        return ColumnSourceType.VARCHAR
    elif db_type_upper in ['CHAR', 'CHARACTER', 'BPCHAR']:
        return ColumnSourceType.CHAR
    elif db_type_upper in ['TEXT', 'LONGTEXT', 'MEDIUMTEXT', 'TINYTEXT']:
        return ColumnSourceType.TEXT
    elif db_type_upper in ['CLOB']:
        return ColumnSourceType.CLOB
    elif db_type_upper in ['NVARCHAR']:
        return ColumnSourceType.NVARCHAR
    elif db_type_upper in ['NCHAR']:
        return ColumnSourceType.NCHAR
    elif db_type_upper in ['NTEXT']:
        return ColumnSourceType.NTEXT
    
    # Temporal types
    elif db_type_upper in ['DATE']:
        return ColumnSourceType.DATE
    elif db_type_upper in ['TIME', 'TIME_WITHOUT_TIME_ZONE']:
        return ColumnSourceType.TIME
    elif db_type_upper in ['DATETIME', 'TIMESTAMP', 'TIMESTAMP_WITHOUT_TIME_ZONE']:
        return ColumnSourceType.TIMESTAMP
    elif db_type_upper in ['TIMESTAMPTZ', 'TIMESTAMP_WITH_TIME_ZONE', 'TIMESTAMPTZ']:
        return ColumnSourceType.TIMESTAMPTZ
    elif db_type_upper in ['INTERVAL']:
        return ColumnSourceType.INTERVAL
    elif db_type_upper in ['YEAR']:
        return ColumnSourceType.YEAR
    
    # Boolean types
    elif db_type_upper in ['BOOLEAN', 'BOOL']:
        return ColumnSourceType.BOOLEAN
    elif db_type_upper in ['BIT']:
        return ColumnSourceType.BIT
    
    # Binary types
    elif db_type_upper in ['BINARY']:
        return ColumnSourceType.BINARY
    elif db_type_upper in ['VARBINARY']:
        return ColumnSourceType.VARBINARY
    elif db_type_upper in ['BLOB', 'LONGBLOB', 'MEDIUMBLOB', 'TINYBLOB']:
        return ColumnSourceType.BLOB
    elif db_type_upper in ['BYTEA']:
        return ColumnSourceType.BYTEA
    
    # JSON types
    elif db_type_upper in ['JSON']:
        return ColumnSourceType.JSON
    elif db_type_upper in ['JSONB']:
        return ColumnSourceType.JSONB
    elif db_type_upper in ['XML']:
        return ColumnSourceType.XML
    
    # UUID types
    elif db_type_upper in ['UUID']:
        return ColumnSourceType.UUID
    elif db_type_upper in ['UNIQUEIDENTIFIER']:
        return ColumnSourceType.UNIQUEIDENTIFIER
    
    # Array types
    elif db_type_upper.endswith('[]') or 'ARRAY' in db_type_upper:
        return ColumnSourceType.ARRAY
    
    # Enum types
    elif db_type_upper in ['ENUM']:
        return ColumnSourceType.ENUM
    elif db_type_upper in ['SET']:
        return ColumnSourceType.SET
    
    # Spatial types
    elif db_type_upper in ['GEOMETRY']:
        return ColumnSourceType.GEOMETRY
    elif db_type_upper in ['GEOGRAPHY']:
        return ColumnSourceType.GEOGRAPHY
    elif db_type_upper in ['POINT']:
        return ColumnSourceType.POINT
    elif db_type_upper in ['POLYGON']:
        return ColumnSourceType.POLYGON
    
    # Additional common types
    elif db_type_upper in ['SERIAL4']:
        return ColumnSourceType.INTEGER
    elif db_type_upper in ['SERIAL8']:
        return ColumnSourceType.BIGINT
    elif db_type_upper in ['FLOAT4']:
        return ColumnSourceType.FLOAT
    elif db_type_upper in ['FLOAT8']:
        return ColumnSourceType.DOUBLE
    elif db_type_upper in ['TEXT']:
        return ColumnSourceType.TEXT
    elif db_type_upper in ['BPCHAR']:
        return ColumnSourceType.CHAR
    elif db_type_upper in ['VARCHAR2']:  # Oracle
        return ColumnSourceType.VARCHAR
    elif db_type_upper in ['NUMBER']:  # Oracle - could be integer or decimal
        return ColumnSourceType.DECIMAL  # Default to decimal, can be refined based on precision/scale
    elif db_type_upper in ['CLOB']:
        return ColumnSourceType.CLOB
    elif db_type_upper in ['BLOB']:
        return ColumnSourceType.BLOB
    elif db_type_upper in ['RAW']:  # Oracle
        return ColumnSourceType.VARBINARY
    elif db_type_upper in ['LONG']:  # Oracle
        return ColumnSourceType.TEXT
    elif db_type_upper in ['LONG RAW']:  # Oracle
        return ColumnSourceType.BLOB
    
    # Default fallback
    else:
        # print(f"Warning: Unknown database type '{db_type_upper}', mapping to UNKNOWN")
        return ColumnSourceType.UNKNOWN


def build_column_source_meta(column: ColumnSchema) -> ColumnSourceMeta:
    """
    Build ColumnSourceMeta from a database ColumnSchema.
    """
    return ColumnSourceMeta(
        max_length=column.max_length,
        precision=column.precision,
        scale=column.scale,
        nullable=column.nullable,
        default_value=column.default_value
    )


def find_column_in_schema(
    table_name: Optional[str], 
    column_name: str, 
    schema: DatabaseSchema
) -> Optional[ColumnSchema]:
    """
    Find a specific column in the database schema.
    """
    for table in schema.tables:
        # If table_name is specified, only search in that table
        if table_name and table.name != table_name:
            continue
            
        for column in table.columns:
            if column.name == column_name:
                return column
    
    return None


def infer_source_type_for_measure(
    measure: SemanticMeasure, 
    schema: DatabaseSchema
) -> tuple[Optional[ColumnSourceType], Optional[ColumnSourceMeta]]:
    """
    Infer source_type and source_meta for a SemanticMeasure by looking up its column in the schema.
    """
    if not measure.query:
        return None, None
    
    # Find the column in the schema
    column = find_column_in_schema(measure.table, measure.query, schema)
    if not column:
        return None, None
    
    # Map database type to our enum
    source_type = map_database_type_to_source_type(column.type)
    source_meta = build_column_source_meta(column)
    
    return source_type, source_meta


def infer_source_type_for_dimension(
    dimension: SemanticDimension, 
    schema: DatabaseSchema
) -> tuple[Optional[ColumnSourceType], Optional[ColumnSourceMeta]]:
    """
    Infer source_type and source_meta for a SemanticDimension by looking up its column in the schema.
    """
    # Find the column in the schema
    column = find_column_in_schema(dimension.table, dimension.query, schema)
    if not column:
        return None, None
    
    # Map database type to our enum
    source_type = map_database_type_to_source_type(column.type)
    source_meta = build_column_source_meta(column)
    
    return source_type, source_meta


def infer_source_type_for_filter(
    filter_obj: SemanticFilter, 
    schema: DatabaseSchema
) -> tuple[Optional[ColumnSourceType], Optional[ColumnSourceMeta]]:
    """
    Infer source_type and source_meta for a SemanticFilter by looking up its column in the schema.
    """
    # Find the column in the schema
    column = find_column_in_schema(filter_obj.table, filter_obj.query, schema)
    if not column:
        return None, None
    
    # Map database type to our enum
    source_type = map_database_type_to_source_type(column.type)
    source_meta = build_column_source_meta(column)
    
    return source_type, source_meta


def auto_infer_semantic_types(
    measures: Optional[List[SemanticMeasure]], 
    dimensions: Optional[List[SemanticDimension]], 
    filters: Optional[List[SemanticFilter]],
    schema: DatabaseSchema
) -> tuple[
    Optional[List[SemanticMeasure]], 
    Optional[List[SemanticDimension]], 
    Optional[List[SemanticFilter]]
]:
    """
    Auto-infer source_type and source_meta for all measures, dimensions, and filters
    by looking up their columns in the database schema.
    """
    # Process measures
    updated_measures = None
    if measures:
        updated_measures = []
        for measure in measures:
            source_type, source_meta = infer_source_type_for_measure(measure, schema)
            # Create a copy with updated fields
            updated_measure = measure.model_copy()
            updated_measure.source_type = source_type
            updated_measure.source_meta = source_meta
            updated_measures.append(updated_measure)
    
    # Process dimensions
    updated_dimensions = None
    if dimensions:
        updated_dimensions = []
        for dimension in dimensions:
            source_type, source_meta = infer_source_type_for_dimension(dimension, schema)
            # Create a copy with updated fields
            updated_dimension = dimension.model_copy()
            updated_dimension.source_type = source_type
            updated_dimension.source_meta = source_meta
            updated_dimensions.append(updated_dimension)
    
    # Process filters
    updated_filters = None
    if filters:
        updated_filters = []
        for filter_obj in filters:
            source_type, source_meta = infer_source_type_for_filter(filter_obj, schema)
            # Create a copy with updated fields
            updated_filter = filter_obj.model_copy()
            updated_filter.source_type = source_type
            updated_filter.source_meta = source_meta
            updated_filters.append(updated_filter)
    
    return updated_measures, updated_dimensions, updated_filters
