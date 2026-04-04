import pytest
from db.models import Review, get_db_session, init_db, engine, Base
from sqlalchemy import text
from unittest.mock import patch
import os

def test_review_repr():
    """測試 Review 模型的 __repr__"""
    review = Review(id=1, project="Test", verdict="OK")
    assert "<Review(id=1, project='Test', verdict='OK')>" in repr(review)

def test_get_db_session():
    """測試資料庫 Session 產生器"""
    session_gen = get_db_session()
    db = next(session_gen)
    assert db is not None
    # 執行一個簡單查詢確保連線正常
    db.execute(text("SELECT 1"))
    
    # 結束後關閉
    with pytest.raises(StopIteration):
        next(session_gen)

def test_init_db():
    """測試資料庫初始化"""
    init_db()
    # 檢查 table 是否存在
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'"))
        assert result.fetchone() is not None

def test_engine_creation_branches(monkeypatch):
    """測試 engine 建立的不同分支 (PostgreSQL)"""
    from db.models import create_db_engine
    
    with patch("db.models.create_engine") as mock_create:
        # 測試 Postgres 分支
        create_db_engine("postgresql://user:pass@localhost/db")
        assert mock_create.called
        args, kwargs = mock_create.call_args
        assert args[0].startswith("postgresql")
        assert "pool_size" in kwargs
        
        # 測試其他非 Postgres URL 分支
        create_db_engine("mysql://user:pass@localhost/db")
        assert mock_create.call_count == 2
        
        # 測試預設 SQLite 分支
        create_db_engine(None)
        assert mock_create.call_count == 3
        # Ensure it uses connect_args for sqlite
        args, kwargs = mock_create.call_args
        assert "sqlite" in args[0] or "check_same_thread" in kwargs.get("connect_args", {})
