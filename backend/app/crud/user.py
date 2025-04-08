from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate


def get_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_id: int
        User ID
        
    Returns:
    --------
    Optional[User]
        User if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Parameters:
    -----------
    db: Session
        Database session
    email: str
        User email
        
    Returns:
    --------
    Optional[User]
        User if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Parameters:
    -----------
    db: Session
        Database session
    username: str
        Username
        
    Returns:
    --------
    Optional[User]
        User if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def create(db: Session, *, obj_in: UserCreate) -> User:
    """
    Create new user.
    
    Parameters:
    -----------
    db: Session
        Database session
    obj_in: UserCreate
        User creation data
        
    Returns:
    --------
    User
        Created user
    """
    db_obj = User(
        email=obj_in.email,
        username=obj_in.username,
        hashed_password=get_password_hash(obj_in.password),
        full_name=obj_in.full_name,
        is_superuser=obj_in.is_superuser,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(
    db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
) -> User:
    """
    Update user.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_obj: User
        User to update
    obj_in: Union[UserUpdate, Dict[str, Any]]
        User update data
        
    Returns:
    --------
    User
        Updated user
    """
    obj_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
    if "password" in obj_data and obj_data["password"]:
        hashed_password = get_password_hash(obj_data["password"])
        del obj_data["password"]
        obj_data["hashed_password"] = hashed_password
    for field in obj_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, obj_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def authenticate(db: Session, *, email: str, password: str) -> Optional[User]:
    """
    Authenticate user.
    
    Parameters:
    -----------
    db: Session
        Database session
    email: str
        User email
    password: str
        User password
        
    Returns:
    --------
    Optional[User]
        User if authentication successful, None otherwise
    """
    user = get_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def is_active(user: User) -> bool:
    """
    Check if user is active.
    
    Parameters:
    -----------
    user: User
        User to check
        
    Returns:
    --------
    bool
        True if user is active, False otherwise
    """
    return user.is_active


def is_superuser(user: User) -> bool:
    """
    Check if user is superuser.
    
    Parameters:
    -----------
    user: User
        User to check
        
    Returns:
    --------
    bool
        True if user is superuser, False otherwise
    """
    return user.is_superuser