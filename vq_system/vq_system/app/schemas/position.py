from pydantic import BaseModel
from typing import Optional

class PositionUpsert(BaseModel):
    topic_id: int
    department_id: int
    content: Optional[str] = None
    client_version: int

class PositionOut(BaseModel):
    id: int
    topic_id: int
    department_id: int
    content: Optional[str] = None
    version: int
    last_updated_by: Optional[int] = None

    class Config:
        from_attributes = True

class PositionHistoryOut(BaseModel):
    id: int
    position_id: int
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_version: int
    new_version: int
    changed_by: Optional[int] = None

    class Config:
        from_attributes = True
