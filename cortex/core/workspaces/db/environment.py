from datetime import datetime

import pytz
from sqlalchemy import String, DateTime, ForeignKey, UUID
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel


class WorkspaceEnvironmentORM(BaseDBModel):
    __tablename__ = "environments"
    id = mapped_column(UUID, primary_key=True, index=True)
    workspace_id = mapped_column(UUID, ForeignKey("workspaces.id"), nullable=False, index=True)
    name = mapped_column(String, default="Development", index=True)
    description = mapped_column(
        String, 
        default="Default environment for workspace",
        nullable=True,
        index=False
    )
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))
