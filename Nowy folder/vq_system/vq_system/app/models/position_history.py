from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
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
