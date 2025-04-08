from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    id: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    created_at: datetime
    
    class Config:
        orm_mode = True