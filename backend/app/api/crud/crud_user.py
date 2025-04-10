from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_id: int
        User ID
        
    Returns:
    --------
    Optional[User]
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Parameters:
    -----------
    db: Session
        Database session
    username: str
        Username
        
    Returns:
    --------
    Optional[User]
        User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Parameters:
    -----------
    db: Session
        Database session
    email: str
        Email
        
    Returns:
    --------
    Optional[User]
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get multiple users with pagination.
    
    Parameters:
    -----------
    db: Session
        Database session
    skip: int
        Number of records to skip
    limit: int
        Maximum number of records to return
        
    Returns:
    --------
    List[User]
        List of users
    """
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user.
    
    Parameters:
    -----------
    db: Session
        Database session
    user_in: UserCreate
        User creation data
        
    Returns:
    --------
    User
        Created user
    """
    # Create the user object
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser
    )
    
    # Add to the database and commit
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user(db: Session, db_user: User, user_in: Union[UserUpdate, Dict[str, Any]]) -> User:
    """
    Update a user.
    
    Parameters:
    -----------
    db: Session
        Database session
    db_user: User
        Existing user object
    user_in: Union[UserUpdate, Dict[str, Any]]
        User update data
        
    Returns:
    --------
    User
        Updated user
    """
    # Convert to dict if not already
    update_data = user_in if isinstance(user_in, dict) else user_in.dict(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    # Update the user object
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    # Commit the changes
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def authenticate(db: Session, email: str, password: str) -> Optional[User]:
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
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user



def is_active(user: User) -> bool:
    """
    Check if a user is active.
    
    Parameters:
    -----------
    user: User
        User object
        
    Returns:
    --------
    bool
        True if the user is active, False otherwise
    """
    return user.is_active


def is_superuser(user: User) -> bool:
    """
    Check if a user is a superuser.
    
    Parameters:
    -----------
    user: User
        User object
        
    Returns:
    --------
    bool
        True if the user is a superuser, False otherwise
    """
    return user.is_superuser