from typing import List

from cortex.core.types.sql_schema import DatabaseSchema, TableSchema, ColumnSchema, ForeignKeySchema
from cortex.core.types.telescope import TSModel


class SchemaHumanizer(TSModel):
    """
    Converts database schema information into human-readable descriptions.
    """
    
    def humanize_schema(self, schema: DatabaseSchema) -> str:
        """
        Convert a complete database schema into a human-readable markdown description.
        
        Args:
            schema: The database schema object to humanize
            
        Returns:
            A markdown-formatted string description of the database schema
        """
        if not schema.tables:
            return "## Database Schema\n\nThis database contains no tables."
        
        description_parts = [
            "# Database Schema",
            "",
            f"This database contains **{len(schema.tables)}** table{'s' if len(schema.tables) != 1 else ''}.",
            ""
        ]
        
        for table in schema.tables:
            table_description = self._humanize_table(table)
            description_parts.append(table_description)
            description_parts.append("")  # Add spacing between tables
        
        return "\n".join(description_parts).strip()
    
    def _humanize_table(self, table: TableSchema) -> str:
        """
        Convert a single table schema into a markdown-formatted description.
        """
        lines = [f"## Table: `{table.name}`"]
        
        # Describe columns
        if table.columns:
            lines.append("")
            lines.append(f"Contains **{len(table.columns)}** column{'s' if len(table.columns) != 1 else ''}:")
            lines.append("")
            
            for column in table.columns:
                column_desc = self._humanize_column(column)
                lines.append(f"- {column_desc}")
        else:
            lines.append("")
            lines.append("Contains no columns.")
        
        # Describe primary keys
        if table.primary_keys:
            lines.append("")
            if len(table.primary_keys) == 1:
                lines.append(f"**Primary key:** `{table.primary_keys[0]}`")
            else:
                keys_str = "`, `".join(table.primary_keys)
                lines.append(f"**Primary keys:** `{keys_str}`")
        
        # Describe foreign key relationships
        if table.foreign_keys:
            lines.append("")
            lines.append("**Foreign key relationships:**")
            for fk in table.foreign_keys:
                fk_desc = self._humanize_foreign_key(fk)
                lines.append(f"- {fk_desc}")
        
        return "\n".join(lines)
    
    def _humanize_column(self, column: ColumnSchema) -> str:
        """
        Convert a single column schema into a markdown-formatted description.
        """
        # Start with column name and type
        description_parts = [f"`{column.name}` ({self._format_column_type(column)})"]
        
        # Add nullability information
        if column.nullable is not None:
            if column.nullable:
                description_parts.append("*can be empty*")
            else:
                description_parts.append("**required**")
        
        # Add default value information
        if column.default_value is not None:
            description_parts.append(f"default: `{column.default_value}`")
        
        return " - ".join(description_parts)
    
    def _format_column_type(self, column: ColumnSchema) -> str:
        """
        Format the column type with its constraints in a markdown-friendly way.
        """
        type_parts = [f"`{column.type}`"]
        
        # Add length/size information
        if column.max_length is not None:
            type_parts.append(f"max length: `{column.max_length}`")
        
        # Add precision and scale for numeric types
        if column.precision is not None:
            if column.scale is not None:
                type_parts.append(f"precision: `{column.precision}`, scale: `{column.scale}`")
            else:
                type_parts.append(f"precision: `{column.precision}`")
        elif column.scale is not None:
            type_parts.append(f"scale: `{column.scale}`")
        
        if len(type_parts) == 1:
            return type_parts[0]
        else:
            return f"{type_parts[0]} - {', '.join(type_parts[1:])}"
    
    def _humanize_foreign_key(self, foreign_key: ForeignKeySchema) -> str:
        """
        Convert a foreign key relationship into a markdown-formatted description.
        """
        if not foreign_key.relations:
            return "*Invalid foreign key relationship*"
        
        if len(foreign_key.relations) == 1:
            relation = foreign_key.relations[0]
            return f"`{relation.column}` references `{relation.referenced_table}.{relation.referenced_column}`"
        else:
            # Multiple relations in a foreign key
            relation_descriptions = []
            for relation in foreign_key.relations:
                relation_descriptions.append(f"`{relation.column}` → `{relation.referenced_table}.{relation.referenced_column}`")
            return f"**Composite foreign key:** {', '.join(relation_descriptions)}" 