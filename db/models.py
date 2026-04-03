"""
SQLAlchemy ORM Models for DSS Database
支援 SQLite 與 PostgreSQL 雙重後端
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL configuration (default to SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db/history.db")

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    # PostgreSQL settings with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True  # Enable connection health checks
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Review(Base):
    """Review ORM Model - maps to reviews table"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    project = Column(String(500), nullable=False)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    risk_high = Column(Integer, default=0)
    risk_medium = Column(Integer, default=0)
    risk_low = Column(Integer, default=0)
    verdict = Column(Text)
    result_json = Column(JSON, nullable=False)
    
    def __repr__(self):
        return f"<Review(id={self.id}, project='{self.project}', verdict='{self.verdict}')>"


def get_db_session():
    """Get database session (for use in FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database schema"""
    Base.metadata.create_all(bind=engine)
