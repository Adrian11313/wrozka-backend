from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    department_id: Optional[int] = None
    role: str = "user"

class UserOut(BaseModel):
    id: int
    username: str
    department_id: Optional[int] = None
    role: str

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
