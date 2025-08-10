import json
import os
import base64
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from cortex.core.stores.sqlalchemy import BaseDBModel


def json_default_encoder(val):
    """General JSON encoder for non-serializable types.

    Handles common Python types that need conversion:
    - datetime/date -> ISO 8601 strings
    - UUID -> str
    - Decimal -> float
    - set -> list
    - bytes -> utf-8 string if decodable, else base64
    - Enum -> value
    """
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, Decimal):
        # Convert to float for JSON compatibility
        return float(val)
    if isinstance(val, set):
        return list(val)
    if isinstance(val, bytes):
        try:
            return val.decode("utf-8")
        except Exception:
            return base64.b64encode(val).decode("ascii")
    if isinstance(val, Enum):
        return val.value
    raise TypeError(f"Object of type {type(val).__name__} is not JSON serializable")


def dumps(d):
    return json.dumps(d, default=json_default_encoder)


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
