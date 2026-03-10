from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str

class ProjectOut(BaseModel):
    id: int
    name: str
    status: str

    class Config:
        from_attributes = True
