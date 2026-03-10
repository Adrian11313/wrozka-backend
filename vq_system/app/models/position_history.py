from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from app.models.base import Base

class PositionHistory(Base):
    __tablename__ = "position_history"

    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)

    old_content = Column(Text, nullable=True)
    new_content = Column(Text, nullable=True)

    old_version = Column(Integer, nullable=False)
    new_version = Column(Integer, nullable=False)

    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    changed_at = Column(DateTime, server_default=func.now(), nullable=False)
    old_status = Column(String)
    new_status = Column(String)
    old_priority = Column(String)
    new_priority = Column(String)
    old_owner = Column(String)
    new_owner = Column(String)
    old_due_date = Column(String)
    new_due_date = Column(String)
