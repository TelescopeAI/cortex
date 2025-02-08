from typing import List

from core.types.telescope import TSModel


class ColumnSchema(TSModel):
    name: str
    type: str


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
