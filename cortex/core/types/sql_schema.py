from typing import List, Optional

from cortex.core.types.telescope import TSModel


class ColumnSchema(TSModel):
    name: str
    type: str
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    nullable: Optional[bool] = None
    default_value: Optional[str] = None


class ForeignKeyRelation(TSModel):
    column: str
    referenced_table: str
    referenced_column: str


class ForeignKeySchema(TSModel):
    table: str
    relations: List[ForeignKeyRelation]


class TableSchema(TSModel):
    name: str
    columns: List[ColumnSchema]
    primary_keys: List[str]
    foreign_keys: List[ForeignKeySchema]


class DatabaseSchema(TSModel):
    tables: List[TableSchema]
