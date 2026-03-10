from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # temporarily without FK (prevents NoReferencedTableError during flush on your setup)
    department_id = Column(Integer, nullable=True)

    role = Column(String(50), default="user")  # admin|coordinator|user|readonly
    created_at = Column(DateTime, server_default=func.now())
