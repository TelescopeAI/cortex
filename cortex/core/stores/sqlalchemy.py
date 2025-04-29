from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

# from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "postgresql://root:password@localhost:5432/core"
#
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
metadata = MetaData(naming_convention=POSTGRES_INDEXES_NAMING_CONVENTION)


class BaseDBModel(DeclarativeBase):
    naming_convention = POSTGRES_INDEXES_NAMING_CONVENTION
