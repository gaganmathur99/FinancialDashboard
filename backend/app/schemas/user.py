from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    email: str
    username: str
    password: str


class UserUpdate(UserBase):
    """User update schema"""
    password: Optional[str] = None


class UserInDBBase(UserBase):
    """User in DB schema"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDBBase):
    """User schema (returned to client)"""
    pass


class UserInDB(UserInDBBase):
    """User in DB schema (with hashed password)"""
    hashed_password: str