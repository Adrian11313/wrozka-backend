from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.models.base import Base

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("topic_id", "department_id", name="uq_positions_topic_department"),
    )

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    content = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    last_updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
