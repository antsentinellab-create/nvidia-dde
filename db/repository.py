"""
DB 存取層（Repository Pattern）
cli.py 不應直接操作 sqlite3，統一透過這個模組
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "history.db"


def save_review(project_name: str, result_json: dict) -> int:
    """儲存審查結果，回傳新建的 review id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    risks = result_json.get("risks", [])
    risk_high   = sum(1 for r in risks if r.get("level") == "high")
    risk_medium = sum(1 for r in risks if r.get("level") == "medium")
    risk_low    = sum(1 for r in risks if r.get("level") == "low")
    verdict     = result_json.get("verdict", "")[:500]

    cursor.execute("""
        INSERT INTO reviews
            (project, reviewed_at, risk_high, risk_medium, risk_low, verdict, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project_name,
        datetime.utcnow().isoformat(),
        risk_high, risk_medium, risk_low,
        verdict,
        json.dumps(result_json, ensure_ascii=False)
    ))

    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id


def get_recent_reviews(limit: int = 10) -> list:
    """查詢最近 N 筆記錄"""
    if not DB_PATH.exists():
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict
        FROM reviews
        ORDER BY reviewed_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows
