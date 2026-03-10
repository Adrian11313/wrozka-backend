from pydantic import BaseModel
from typing import Optional

class TopicCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None

class TopicOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
