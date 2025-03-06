import json
import os
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.stores.sqlalchemy import BaseDBModel


def date_time_encoder(val):
    if isinstance(val, datetime):
        return val.isoformat()
    raise TypeError()


def dumps(d):
    return json.dumps(d, default=date_time_encoder)


class Connection:
    def __init__(self):
        self.db_type = os.getenv('CORE_DB_TYPE')
        self.db_username = os.getenv('CORE_DB_USERNAME')
        self.db_password = os.getenv('CORE_DB_PASSWORD')
        self.db_host = os.getenv('CORE_DB_HOST')
        self.db_port = os.getenv('CORE_DB_PORT')
        self.db_name = os.getenv('CORE_DB_NAME')
        self.db_url = f"{self.db_type}://{self.db_username}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        self.engine = create_engine(url=self.db_url, pool_size=50, max_overflow=10, json_serializer=dumps)
        session_maker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.SessionLocal = session_maker()
        self.Base = BaseDBModel


class LocalSession(Connection):
    def __init__(self):
        Connection.__init__(self)
        self.connection = Connection()
        self.session: Session = self.connection.SessionLocal

    def get_session(self):
        return self.session

    def close_session(self):
        self.session.close()

    def get_table_names(self):
        return self.engine.table_names()

    def reflect_on_db(self):
        return self.Base.metadata.reflect(self.engine)

    def create_all_tables(self):
        self.Base.metadata.create_all(bind=self.engine)

    def drop_all_tables(self):
        self.Base.metadata.drop_all(bind=self.engine)

    # def get_schema_dump(self):
    #     inspector = Inspector.from_engine(self.engine)
    #
    #     schema_list = []
    #     for table_name in inspector.get_table_names():
    #         columns = []
    #         for column in inspector.get_columns(table_name):
    #             columns.append({"name": column["name"], "definition": str(column["type"])})
    #         schema_list.append({"name": table_name, "columns": columns})
    #     return schema_list
