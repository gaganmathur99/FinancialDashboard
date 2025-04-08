from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.api.schemas.user import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash, verify_password

def get(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()

def get_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()

def get_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()

def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get all users with pagination
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[User]: List of users
    """
    return db.query(User).offset(skip).limit(limit).all()

def create(db: Session, obj_in: UserCreate) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        obj_in: User data
        
    Returns:
        User: Created user
    """
    db_obj = User(
        username=obj_in.username,
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        is_active=True,
        is_admin=obj_in.is_admin
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update(db: Session, db_obj: User, obj_in: UserUpdate) -> User:
    """
    Update a user
    
    Args:
        db: Database session
        db_obj: User object to update
        obj_in: User data
        
    Returns:
        User: Updated user
    """
    update_data = obj_in.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete(db: Session, user_id: int) -> bool:
    """
    Delete a user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        bool: True if deleted, False otherwise
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user
    
    Args:
        db: Database session
        username: Username
        password: Plain text password
        
    Returns:
        User: User object if authentication successful, None otherwise
    """
    user = get_by_username(db, username=username)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user