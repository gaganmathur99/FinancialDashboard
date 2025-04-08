import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings


# Create database engine
engine = sqlalchemy.create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Get database session.
    
    Yields:
    -------
    Session
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()