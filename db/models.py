"""
SQLAlchemy ORM Models for DSS Database
支援 SQLite 與 PostgreSQL 雙重後端
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_db_engine(url: Optional[str] = None):
    """根據 URL 建立資料庫引擎"""
    if url:
        if url.startswith("postgresql"):
            return create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
        return create_engine(url)
    
    # 預設使用 SQLite
    return create_engine(
        "sqlite:///db/history.db", 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

# 建立全域引擎與 Session
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_db_engine(DATABASE_URL)
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
