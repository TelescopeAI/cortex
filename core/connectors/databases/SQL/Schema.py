from typing import List

from sqlalchemy import create_engine, MetaData

from core.types.sql_schema import ForeignKeySchema, ForeignKeyRelation, DatabaseSchema, TableSchema, ColumnSchema


def create_db_url(db_type: str, username: str, password: str, host: str, port: str, db_name: str) -> str:
    return f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"


def get_foreign_keys_schema(table) -> List[ForeignKeySchema]:
    foreign_keys_list = []
    for column in table.columns:
        for fk in column.foreign_keys:
            relation = ForeignKeyRelation(
                column=column.name,
                referenced_table=fk.column.table.name,
                referenced_column=fk.column.name
            )
            foreign_key_schema = ForeignKeySchema(
                table=table.name,
                relations=[relation]
            )
            foreign_keys_list.append(foreign_key_schema)
    return foreign_keys_list


def get_sql_schema(database_url: str, include_views: bool = False) -> DatabaseSchema:
    engine = create_engine(database_url, echo=True)
    metadata = MetaData()
    # print("Starting metadata reflection")
    if include_views:
        metadata.reflect(engine, views=True)
    else:
        metadata.reflect(engine)

    tables_list: List[TableSchema] = []

    for table in metadata.tables.values():
        columns = [ColumnSchema(name=col.name, type=str(col.type)) for col in table.columns]
        primary_keys = [pk.name for pk in table.primary_key]
        foreign_keys_list = get_foreign_keys_schema(table)

        table_schema = TableSchema(
            name=table.name,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys_list
        )

        tables_list.append(table_schema)

    return DatabaseSchema(tables=tables_list)


# Example Usage
if __name__ == '__main__':
    db_url = create_db_url('postgresql', 'root', 'password', 'localhost', '5432', 'core')
    schema = get_sql_schema(db_url, True)
    print(f' {schema.tables[0].columns}')
    print(f"JSON Schema: \n {schema.json()}", )
    # Usage example
    # model_generator = CubeJsModelGenerator(database_schema=schema)
    # cube_js_yaml = model_generator.generate_yaml()
    # print(f"YAML Schema: \n {cube_js_yaml}")
    # print(schema.json())