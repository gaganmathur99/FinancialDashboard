from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    """Base schema for user data."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_admin: Optional[bool] = False

class UserCreate(UserBase):
    """Schema for creating a user."""
    username: str
    email: EmailStr
    password: str

class UserUpdate(UserBase):
    """Schema for updating a user."""
    password: Optional[str] = None

class UserResponse(UserBase):
    """Schema for user response."""
    id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str