from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func

from backend.app.db.base import Base


class User(Base):
    """
    User model for database.
    
    Attributes:
    -----------
    id: int
        User ID
    email: str
        User email
    username: str
        Username
    full_name: str
        User's full name
    hashed_password: str
        Hashed password
    is_active: bool
        Whether the user is active
    is_superuser: bool
        Whether the user is a superuser
    created_at: datetime
        Creation timestamp
    updated_at: datetime
        Last update timestamp
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())