"""
Database Configuration
SQLAlchemy setup for PostgreSQL connection
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Database URL from environment variable or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/quran_app"
)

# Create engine
engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
