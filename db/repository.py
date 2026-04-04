"""
DB 存取層（Repository Pattern）
cli.py 不應直接操作 sqlite3，統一透過這個模組
現改用 SQLAlchemy ORM，支援 SQLite/PostgreSQL 雙後端
"""
import json
from datetime import datetime
from db.models import Review, SessionLocal, init_db


def save_review(project_name: str, result_json: dict) -> int:
    """儲存審查結果，回傳新建的 review id"""
    db = SessionLocal()
    try:
        risks = result_json.get("risks", [])
        risk_high   = sum(1 for r in risks if r.get("level") == "high")
        risk_medium = sum(1 for r in risks if r.get("level") == "medium")
        risk_low    = sum(1 for r in risks if r.get("level") == "low")
        verdict     = result_json.get("verdict", "")[:500]
        
        review = Review(
            project=project_name,
            reviewed_at=datetime.utcnow(),
            risk_high=risk_high,
            risk_medium=risk_medium,
            risk_low=risk_low,
            verdict=verdict,
            result_json=result_json
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        return review.id
    finally:
        db.close()


def get_recent_reviews(limit: int = 10) -> list:
    """查詢最近 N 筆記錄"""
    db = SessionLocal()
    try:
        reviews = db.query(Review).order_by(Review.reviewed_at.desc()).limit(limit).all()
        # Return as tuples to maintain backward compatibility
        result = [
            (r.id, r.project, r.reviewed_at, r.risk_high, r.risk_medium, r.risk_low, r.verdict)
            for r in reviews
        ]
        return result
    finally:
        db.close()


def get_review_by_id(review_id: int) -> dict:
    """根據 ID 獲取審查詳情"""
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            return {
                "id": review.id,
                "project": review.project,
                "reviewed_at": review.reviewed_at.isoformat() if review.reviewed_at else None,
                "risk_high": review.risk_high,
                "risk_medium": review.risk_medium,
                "risk_low": review.risk_low,
                "verdict": review.verdict,
                "result_json": review.result_json,
                # 添加預先格式化的 JSON 字串（支援中文）
                "result_json_formatted": json.dumps(review.result_json, indent=2, ensure_ascii=False)
            }
        return None
    finally:
        db.close()
