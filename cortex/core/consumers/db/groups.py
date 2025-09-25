from datetime import datetime
import pytz
from sqlalchemy import String, JSON, ForeignKey, Table, Column, DateTime, UUID
from sqlalchemy.orm import mapped_column, relationship

from cortex.core.storage.sqlalchemy import BaseDBModel

# Association table for many-to-many relationship
consumer_group_members = Table(
    "consumer_group_members",
    BaseDBModel.metadata,
    Column("consumer_id", UUID, ForeignKey("consumers.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", UUID, ForeignKey("consumer_groups.id", ondelete="CASCADE"), primary_key=True)
)


class ConsumerGroupORM(BaseDBModel):
    __tablename__ = "consumer_groups"

    id = mapped_column(UUID, primary_key=True, index=True)
    environment_id = mapped_column(UUID, ForeignKey("environments.id"), nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    description = mapped_column(String, nullable=True)
    alias = mapped_column(String, nullable=True)
    properties = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime, default=datetime.now(pytz.UTC))
    updated_at = mapped_column(DateTime, default=datetime.now(pytz.UTC), onupdate=datetime.now(pytz.UTC))

    # Relationship to consumers through the association table
    consumers = relationship("ConsumerORM", secondary=consumer_group_members, backref="groups")