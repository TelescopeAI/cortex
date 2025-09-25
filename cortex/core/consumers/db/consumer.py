from datetime import datetime

import pytz
from sqlalchemy import String, DateTime, ForeignKey, UUID, JSON
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel


class ConsumerORM(BaseDBModel):
    __tablename__ = "consumers"
    id = mapped_column(UUID, primary_key=True, index=True)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False, index=True)
    organization = mapped_column(String, nullable=True)
    properties = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))