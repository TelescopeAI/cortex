from datetime import datetime

import pytz
from sqlalchemy import String, Text, DateTime, Float, Boolean, JSON, UUID
from sqlalchemy.orm import mapped_column

from cortex.core.storage.sqlalchemy import BaseDBModel


class QueryHistoryORM(BaseDBModel):
    """ORM model for query_history table."""
    __tablename__ = "query_history"
    
    id = mapped_column(UUID, primary_key=True, index=True)
    metric_id = mapped_column(UUID, nullable=False, index=True)
    data_model_id = mapped_column(UUID, nullable=False, index=True)
    query = mapped_column(Text, nullable=False)
    parameters = mapped_column(JSON, nullable=True)
    context_id = mapped_column(String(255), nullable=True, index=True)
    meta = mapped_column(JSON, nullable=True)
    cache_mode = mapped_column(String(50), nullable=True, index=True)
    query_hash = mapped_column(String(255), nullable=True, index=True)
    duration = mapped_column(Float, nullable=False)
    row_count = mapped_column(Float, nullable=True)
    success = mapped_column(Boolean, nullable=False, index=True)
    error_message = mapped_column(Text, nullable=True)
    executed_at = mapped_column(DateTime, nullable=False, index=True, default=datetime.now(pytz.UTC))
