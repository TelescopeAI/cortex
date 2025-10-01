from datetime import datetime

import pytz
from sqlalchemy import String, DateTime, UUID
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel


class WorkspaceORM(BaseDBModel):
    __tablename__ = "workspaces"
    id = mapped_column(UUID, primary_key=True, index=True)
    name = mapped_column(String, index=True)
    description = mapped_column(String, nullable=True, index=False)
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))
