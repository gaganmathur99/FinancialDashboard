from sqlalchemy.orm import Session

from backend.app.api.crud.crud_user import get_user_by_email, create_user
from backend.app.core.config import settings
from backend.app.db.base import Base, engine
from backend.app.schemas.user import UserCreate


def init_db(db: Session) -> None:
    """
    Initialize the database.
    
    Parameters:
    -----------
    db: Session
        Database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to create a superuser
    user = get_user_by_email(db, email="admin@example.com")
    if not user:
        user_in = UserCreate(
            email="admin@example.com",
            username="admin",
            password="adminpassword",
            is_superuser=True,
        )
        user = create_user(db, user_in=user_in)