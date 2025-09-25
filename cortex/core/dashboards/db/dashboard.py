from datetime import datetime

import pytz
from sqlalchemy import String, DateTime, UUID, Integer, Text, JSON
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel


class DashboardORM(BaseDBModel):
    """ORM model for dashboard table."""
    __tablename__ = "dashboards"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    environment_id = mapped_column(UUID, nullable=False, index=True)
    name = mapped_column(String(255), nullable=False, index=True)
    description = mapped_column(Text, nullable=True)
    type = mapped_column(String(50), nullable=False)
    # Default view reference can be UUID (as string) or an alias string
    default_view = mapped_column(String(255), nullable=False)
    tags = mapped_column(JSON, nullable=True)
    created_by = mapped_column(UUID, nullable=False)
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))
    last_viewed_at = mapped_column(DateTime, nullable=True)
    # Entire dashboard configuration (views, sections, widgets) stored as JSON
    config = mapped_column(JSON, nullable=False, default=dict)


"""
Note: Legacy ORM models for views/sections/widgets were removed in favor of a
single-table design where the entire dashboard configuration is stored in the
"dashboards.config" JSON column. Alembic migrations should drop the legacy
tables if they exist and add the config column to the dashboards table.
"""