"""
SQLite to PostgreSQL Migration Script
將現有 SQLite history.db 資料遷移至 PostgreSQL
"""
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
from db.models import Review, Base, engine as pg_engine


def get_sqlite_connection():
    """獲取 SQLite 連接"""
    db_path = Path(__file__).parent / "history.db"
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    return sqlite3.connect(db_path)


def backup_sqlite_db(backup_path=None):
    """備份 SQLite 資料庫"""
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(__file__).parent / f"history_backup_{timestamp}.db"
    
    db_path = Path(__file__).parent / "history.db"
    shutil.copy2(db_path, backup_path)
    print(f"✓ SQLite 資料庫已備份至：{backup_path}")
    return backup_path


def check_postgresql_empty():
    """檢查 PostgreSQL 是否為空（防止覆蓋現有資料）"""
    from sqlalchemy import text
    
    with pg_engine.connect() as conn:
        # Check if reviews table exists and has data
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'reviews'
            )
        """)).scalar()
        
        if result:
            # Table exists, check if it has data
            count = conn.execute(text("SELECT COUNT(*) FROM reviews")).scalar()
            if count > 0:
                raise ValueError(
                    f"PostgreSQL 資料庫已有 {count} 筆資料，為防止資料遺失，遷移已中止。"
                )
    
    print("✓ PostgreSQL 資料庫檢查通過（空的或無 reviews 表）")


def create_postgresql_schema():
    """建立 PostgreSQL schema"""
    print("正在建立 PostgreSQL schema...")
    Base.metadata.create_all(bind=pg_engine)
    print("✓ PostgreSQL schema 建立完成")


def migrate_data(sqlite_conn, backup_path):
    """執行資料遷移"""
    sqlite_cursor = sqlite_conn.cursor()
    
    # Read all reviews from SQLite
    sqlite_cursor.execute("""
        SELECT id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict, result_json
        FROM reviews
        ORDER BY id
    """)
    
    sqlite_reviews = sqlite_cursor.fetchall()
    print(f"✓ 從 SQLite 讀取 {len(sqlite_reviews)} 筆記錄")
    
    if not sqlite_reviews:
        print("⚠ 沒有需要遷移的資料")
        return 0
    
    # Insert into PostgreSQL
    from sqlalchemy.orm import Session
    from db.models import SessionLocal
    
    migrated_count = 0
    failed_records = []
    
    for row in sqlite_reviews:
        try:
            review_id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict, result_json = row
            
            # Parse datetime
            if isinstance(reviewed_at, str):
                reviewed_at_dt = datetime.fromisoformat(reviewed_at)
            else:
                reviewed_at_dt = reviewed_at
            
            # Parse JSON
            if isinstance(result_json, str):
                result_dict = json.loads(result_json)
            else:
                result_dict = result_json
            
            # Create Review object
            review = Review(
                id=review_id,  # Preserve original ID
                project=project,
                reviewed_at=reviewed_at_dt,
                risk_high=risk_high,
                risk_medium=risk_medium,
                risk_low=risk_low,
                verdict=verdict or "",
                result_json=result_dict
            )
            
            # Insert to PostgreSQL
            db = SessionLocal()
            try:
                # Use merge to preserve ID
                db.merge(review)
                db.commit()
                migrated_count += 1
            except Exception as e:
                db.rollback()
                failed_records.append((review_id, str(e)))
                print(f"✗ 遷移失敗 (ID={review_id}): {e}")
            finally:
                db.close()
                
        except Exception as e:
            failed_records.append((row[0], str(e)))
            print(f"✗ 解析錯誤 (ID={row[0]}): {e}")
    
    return migrated_count, failed_records


def verify_migration(expected_count):
    """驗證遷移結果"""
    from sqlalchemy import text
    
    with pg_engine.connect() as conn:
        actual_count = conn.execute(text("SELECT COUNT(*) FROM reviews")).scalar()
        
        if actual_count == expected_count:
            print(f"✓ 驗證成功：PostgreSQL 有 {actual_count} 筆記錄（與 SQLite 一致）")
            return True
        else:
            print(f"✗ 驗證失敗：SQLite 有 {expected_count} 筆，PostgreSQL 有 {actual_count} 筆")
            return False


def rollback_from_backup(backup_path):
    """從備份還原 SQLite"""
    if backup_path and Path(backup_path).exists():
        db_path = Path(__file__).parent / "history.db"
        shutil.copy2(backup_path, db_path)
        print(f"✓ SQLite 已從備份還原：{backup_path}")


def main():
    """主函數"""
    print("=" * 60)
    print("SQLite to PostgreSQL 遷移工具")
    print("=" * 60)
    print()
    
    # Get database URL
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL", "sqlite:///db/history.db")
    
    if database_url.startswith("sqlite"):
        print("✗ 錯誤：目前使用的是 SQLite，無需遷移")
        print("請在 .env 中設置 PostgreSQL DATABASE_URL")
        return 1
    
    print(f"目標資料庫：{database_url}")
    print()
    
    backup_path = None
    sqlite_conn = None
    
    try:
        # Step 1: Backup SQLite
        print("[1/6] 備份 SQLite 資料庫...")
        backup_path = backup_sqlite_db()
        print()
        
        # Step 2: Check PostgreSQL is empty
        print("[2/6] 檢查 PostgreSQL 資料庫狀態...")
        check_postgresql_empty()
        print()
        
        # Step 3: Create PostgreSQL schema
        print("[3/6] 建立 PostgreSQL schema...")
        create_postgresql_schema()
        print()
        
        # Step 4: Migrate data
        print("[4/6] 遷移資料...")
        sqlite_conn = get_sqlite_connection()
        migrated_count, failed_records = migrate_data(sqlite_conn, backup_path)
        print()
        
        if failed_records:
            print(f"⚠ 遷移過程中有 {len(failed_records)} 筆記錄失敗")
            for review_id, error in failed_records[:5]:  # Show first 5
                print(f"  - ID {review_id}: {error}")
            if len(failed_records) > 5:
                print(f"  ... 還有 {len(failed_records) - 5} 筆")
            print()
        
        # Step 5: Verify migration
        print("[5/6] 驗證遷移結果...")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT COUNT(*) FROM reviews")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        if verify_migration(sqlite_count):
            print()
            print("[6/6] 遷移完成！")
            print()
            print("=" * 60)
            print("✓ 遷移成功完成")
            print("=" * 60)
            print()
            print("下一步:")
            print("1. 確認應用程式能正常連接 PostgreSQL")
            print("2. 測試 Web UI 和 CLI 功能")
            print("3. 確認無誤後可刪除備份檔案")
            print()
            return 0
        else:
            raise Exception("驗證失敗")
            
    except Exception as e:
        print()
        print("=" * 60)
        print("✗ 遷移失敗")
        print("=" * 60)
        print(f"錯誤訊息：{e}")
        print()
        
        # Rollback
        if backup_path:
            print("正在還原 SQLite 備份...")
            rollback_from_backup(backup_path)
        
        return 1
        
    finally:
        if sqlite_conn:
            sqlite_conn.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
