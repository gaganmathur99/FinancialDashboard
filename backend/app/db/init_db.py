from sqlalchemy.orm import Session

from backend.app.db.base import Base, engine
from backend.app.models.user import User
from backend.app.models.bank import BankAccount
from backend.app.core.security import get_password_hash

def init_db(db: Session) -> None:
    """
    Initialize database tables and create initial admin user if needed
    
    Args:
        db: Database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Check if we need to create default admin user
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("adminpassword"),
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)