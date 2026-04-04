import pytest
import json
from datetime import datetime
from db.repository import save_review, get_recent_reviews, get_review_by_id
from db.models import SessionLocal, Review, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    # Ensure clean state
    db = SessionLocal()
    db.query(Review).delete()
    db.commit()
    db.close()

def test_save_review_success():
    """測試成功儲存審查結果"""
    project = "Test Project"
    data = {
        "risks": [
            {"level": "high", "issue": "High risk issue"},
            {"level": "low", "issue": "Low risk issue"}
        ],
        "verdict": "Overall good"
    }
    
    review_id = save_review(project, data)
    assert review_id > 0
    
    # 在資料庫中驗證
    db = SessionLocal()
    review = db.query(Review).get(review_id)
    assert review.project == project
    assert review.risk_high == 1
    assert review.risk_low == 1
    assert review.risk_medium == 0
    assert review.verdict == "Overall good"
    db.close()

def test_get_recent_reviews():
    """測試獲取最近的審查記錄"""
    save_review("P1", {"risks": [], "verdict": "V1"})
    save_review("P2", {"risks": [], "verdict": "V2"})
    
    reviews = get_recent_reviews(limit=10)
    assert len(reviews) == 2
    # 最新的一筆應在最前面 (假設 ID 自增)
    assert reviews[0][1] == "P2"
    assert reviews[1][1] == "P1"
    
    # 測試 limit
    limited = get_recent_reviews(limit=1)
    assert len(limited) == 1

def test_get_review_by_id_found():
    """測試根據 ID 獲取審查詳查"""
    data = {"risks": [{"level": "medium", "issue": "x"}], "verdict": "V"}
    review_id = save_review("Beta", data)
    
    review = get_review_by_id(review_id)
    assert review is not None
    assert review["id"] == review_id
    assert review["project"] == "Beta"
    assert review["risk_medium"] == 1
    assert "result_json_formatted" in review

def test_get_review_by_id_not_found():
    """測試 ID 不存在的情境"""
    review = get_review_by_id(999999)
    assert review is None
