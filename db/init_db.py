#!/usr/bin/env python3
"""
初始化資料庫腳本

執行一次即可建立 db/history.db 與所有必要的表格。
可重複執行（powerful idempotent）。
"""

import sqlite3
from pathlib import Path


def get_db_path() -> Path:
    """取得 db/ 目錄的絕對路徑"""
    current = Path(__file__).resolve()
    return current.parent


def init_database():
    """初始化 SQLite 資料庫"""
    db_path = get_db_path() / "history.db"
    schema_path = get_db_path() / "schema.sql"
    
    print(f"📍 資料庫路徑：{db_path}")
    print(f"📋 Schema 路徑：{schema_path}")
    
    # 連接資料庫（若不存在會自動建立）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 讀取 schema.sql
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到 schema.sql")
        return False
    
    # 執行 DDL
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("✅ 資料庫初始化成功！")
        print(f"   檔案大小：{db_path.stat().st_size} bytes")
        
        # 驗證表格是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   建立表格：{', '.join(tables)}")
        
        # 驗證索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"   建立索引：{', '.join(indexes)}")
        
        return True
    except Exception as e:
        print(f"❌ 錯誤：執行 schema.sql 失敗 - {e}")
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    success = init_database()
    exit(0 if success else 1)
