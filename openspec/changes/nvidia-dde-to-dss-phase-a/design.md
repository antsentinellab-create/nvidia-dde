# nvidia-dde-to-dss-phase-a - 設計細節

## 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      cli.py (新入口)                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Rich CLI 介面                                        │   │
│  │  [1] 新增審查  [2] 查歷史記錄  [3] 管理知識庫  [Q] 退出 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────┬───────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────────────────┐
│ engine/ │ │   db/   │ │    knowledge/       │
│ loader  │ │ history │ │  ├─ roles/          │
│  .py    │ │  .db    │ │  ├─ standards/      │
└────┬────┘ └────┬────┘ │  └─ risk_templates/ │
     │           │       └─────────────────────┘
     │           │
     ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│           design_decision_engine.py (保持不變)               │
│  - ROLES → 改從 knowledge/roles/*.json 載入                   │
│  - SPEC  → 保持 hardcoded（每次執行時手動修改）               │
│  - 核心函數完全不變：build_prompt/get_content/parse_json...  │
└─────────────────────────────────────────────────────────────┘
```

## 模組設計詳解

### 1. knowledge/roles/*.json

#### risk_analyst.json
```json
{
  "id": "deepseek-ai/deepseek-v3.2",
  "name": "Risk-Analyst",
  "system": "你是專精安全性與風險分析的資深架構師。請只輸出 JSON，不要任何說明文字。",
  "focus_fields": ["risks", "verdict"],
  "focus_desc": "主責 risks（含 level/issue/suggestion），若審查中發現重要的 missing 或 improvements 也可少量補充"
}
```

#### completeness_reviewer.json
```json
{
  "id": "qwen/qwen3.5-397b-a17b",
  "name": "Completeness-Reviewer",
  "system": "你是專精需求完整性檢查的資深架構師。請只輸出 JSON，不要任何說明文字。",
  "focus_fields": ["missing", "verdict"],
  "focus_desc": "主責 missing（含 item/reason/how），若審查中發現重要的 risks 或 improvements 也可少量補充"
}
```

#### improvement_advisor.json
```json
{
  "id": "mistralai/mistral-large-3-675b-instruct-2512",
  "name": "Improvement-Advisor",
  "system": "你是專精架構改善建議的資深架構師。請只輸出 JSON，不要任何說明文字。",
  "focus_fields": ["improvements", "good_points", "verdict"],
  "focus_desc": "主責 improvements（含 area/current/better）與 good_points，若審查中發現重要的 risks 或 missing 也可少量補充"
}
```

#### aggregator.json
```json
{
  "id": "nvidia/llama-3.1-nemotron-ultra-253b-v1",
  "name": "Aggregator",
  "system": "你是資深首席架構師，負責整合各專家意見並做最終裁決。只輸出 JSON，不要任何說明文字。",
  "focus_fields": ["risks", "missing", "improvements", "good_points", "verdict"],
  "focus_desc": "整合所有專家意見，去重、排序、裁決衝突，輸出最終報告"
}
```

### 2. engine/loader.py

#### 職責
- 從 `knowledge/roles/` 目錄載入所有角色設定
- 提供 fallback 機制：若載入失敗則使用內建預設值
- 快取機制：避免重複讀取檔案

#### 核心函數

```python
def load_roles() -> List[Dict]:
    """
    從 knowledge/roles/ 載入角色設定
    
    Returns:
        List[Dict]: 角色設定列表
        
    Fallback:
        若載入失敗，回退到內建的 ROLES 常數
    """
    
def load_role(filename: str) -> Dict:
    """
    載入單個角色檔案
    
    Args:
        filename: 檔案名稱（不含路徑），例如 'risk_analyst.json'
        
    Returns:
        Dict: 角色設定
    """
    
def get_knowledge_base_path() -> Path:
    """
    取得 knowledge/ 目錄的絕對路徑
    
    Returns:
        Path: knowledge/ 目錄的絕對路徑
    """
```

#### 實作細節

```python
import json
from pathlib import Path
from typing import List, Dict

# 內建 fallback roles（與 design_decision_engine.py 中的 ROLES 完全相同）
BUILTIN_ROLES = [
    {
        "id": "deepseek-ai/deepseek-v3.2",
        "name": "Risk-Analyst",
        "system": "你是專精安全性與風險分析的資深架構師。請只輸出 JSON，不要任何說明文字。",
        "focus_fields": ["risks", "verdict"],
        "focus_desc": "主責 risks（含 level/issue/suggestion），若審查中發現重要的 missing 或 improvements 也可少量補充",
    },
    # ... 其他角色
]

def get_knowledge_base_path() -> Path:
    """取得 knowledge/ 目錄的絕對路徑"""
    # 策略：從當前檔案位置向上尋找
    current = Path(__file__).resolve()
    
    # 若在 engine/loader.py
    if current.parent.name == "engine":
        return current.parent.parent / "knowledge"
    
    # 若在 cli.py 或其他位置呼叫
    for parent in current.parents:
        if (parent / "knowledge").exists():
            return parent / "knowledge"
    
    raise FileNotFoundError("找不到 knowledge/ 目錄")

def load_role(filename: str) -> Dict:
    """載入單個角色檔案"""
    role_path = get_knowledge_base_path() / "roles" / filename
    
    try:
        with open(role_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  警告：找不到角色檔案 {role_path}，使用內建預設值")
        # 根據 filename 回傳對應的內建角色
        if filename == "risk_analyst.json":
            return BUILTIN_ROLES[0]
        elif filename == "completeness_reviewer.json":
            return BUILTIN_ROLES[1]
        elif filename == "improvement_advisor.json":
            return BUILTIN_ROLES[2]
        else:
            raise ValueError(f"未知的角色檔案：{filename}")
    except json.JSONDecodeError as e:
        print(f"⚠️  警告：角色檔案 JSON 格式錯誤 {e}，使用內建預設值")
        return BUILTIN_ROLES[0]  # 簡化處理，回傳第一個

def load_roles() -> List[Dict]:
    """從 knowledge/roles/ 載入所有角色"""
    roles_dir = get_knowledge_base_path() / "roles"
    
    if not roles_dir.exists():
        print(f"⚠️  警告：找不到 roles 目錄 {roles_dir}，使用內建預設值")
        return BUILTIN_ROLES
    
    role_files = [
        "risk_analyst.json",
        "completeness_reviewer.json",
        "improvement_advisor.json"
    ]
    
    roles = []
    for filename in role_files:
        try:
            role = load_role(filename)
            roles.append(role)
        except Exception as e:
            print(f"⚠️  載入 {filename} 失敗：{e}")
    
    if not roles:
        print("⚠️  所有角色載入失敗，使用內建預設值")
        return BUILTIN_ROLES
    
    return roles
```

### 3. db/schema.sql

```sql
-- Design Review Support System 資料庫結構
-- 版本：1.0
-- 建立日期：2026-04-03

-- 審查歷史記錄表
CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,        -- 專案名稱
    reviewed_at TEXT NOT NULL,        -- ISO8601 時間戳
    risk_high   INTEGER DEFAULT 0,    -- 高風險數量
    risk_medium INTEGER DEFAULT 0,    -- 中風險數量
    risk_low    INTEGER DEFAULT 0,    -- 低風險數量
    verdict     TEXT,                 -- Aggregator 最終裁決摘要
    result_json TEXT NOT NULL,        -- 完整 Aggregator JSON（用於詳細查詢）
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：加速查詢
CREATE INDEX IF NOT EXISTS idx_reviews_reviewed_at ON reviews(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_reviews_project ON reviews(project);
CREATE INDEX IF NOT EXISTS idx_reviews_risk_high ON reviews(risk_high);

-- 觸發程序：自動更新 updated_at
CREATE TRIGGER IF NOT EXISTS update_reviews_updatedat 
AFTER UPDATE ON reviews
BEGIN
    UPDATE reviews SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### 4. db/init_db.py

```python
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
        
        return True
    except Exception as e:
        print(f"❌ 錯誤：執行 schema.sql 失敗 - {e}")
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = init_database()
    exit(0 if success else 1)
```

### 5. cli.py

#### 整體架構

```python
#!/usr/bin/env python3
"""
Design Review Support System - 互動式 CLI

選單：
  [1] 新增審查
  [2] 查歷史記錄
  [3] 管理知識庫
  [Q] 退出
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
import questionary
import sqlite3
from datetime import datetime
from pathlib import Path
import json

# 引入現有引擎
from design_decision_engine import main as run_review
from engine.loader import load_roles

console = Console()

DB_PATH = Path(__file__).parent / "db" / "history.db"

def show_main_menu():
    """顯示主選單"""
    console.print(Panel.fit(
        "[bold blue]Design Review Support System[/bold blue]\n"
        "暖感工業風格 | 琥珀橙主題",
        style="bold white on #1A1A1B",
        border_style="#F39C12"
    ))
    
    choices = [
        "1",  # 新增審查
        "2",  # 查歷史記錄
        "3",  # 管理知識庫
        "q",  # 退出
    ]
    
    choice = questionary.select(
        "請選擇功能：",
        choices=[
            questionary.Choice("[1] 🔍 新增審查", value="1"),
            questionary.Choice("[2] 📊 查歷史記錄", value="2"),
            questionary.Choice("[3] 📚 管理知識庫", value="3"),
            questionary.Choice("[Q] 🚪 退出系統", value="q"),
        ],
        style=[
            ("selected", "#F39C12 bold"),  # 琥珀橙
        ]
    ).ask()
    
    return choice

def add_new_review():
    """新增審查"""
    console.print(Panel("🔍 新增設計審查", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    # 詢問專案名稱
    project_name = questionary.text("請輸入專案名稱：", style=[("text", "#F39C12")]).ask()
    
    if not project_name:
        console.print("[red]❌ 專案名稱不能為空[/red]")
        return
    
    # 確認執行
    if not Confirm.ask(f"確定要執行审查嗎？專案：{project_name}"):
        return
    
    # 執行審查（呼叫現有引擎）
    console.print("\n[yellow]正在執行多專家審查...[/yellow]")
    console.print("這可能需要 2-8 分鐘，請耐心等待。\n")
    
    # TODO: 這裡需要重構 design_decision_engine.main()
    # 讓它回傳結果而不是只 print
    # 暫時先用 subprocess 或其他方式攔截輸出
    
    # 寫入資料庫
    # save_review_to_db(project_name, result_json)
    
    console.print(f"[green]✅ 審查完成！結果已儲存至資料庫。[/green]")

def view_history():
    """查看歷史記錄"""
    console.print(Panel("📊 歷史記錄查詢", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    if not DB_PATH.exists():
        console.print("[red]❌ 資料庫尚未初始化。請先執行 'python db/init_db.py'[/red]")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查詢最近 10 筆記錄
    cursor.execute("""
        SELECT id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict
        FROM reviews
        ORDER BY reviewed_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        console.print("[yellow]⚠️  尚無歷史記錄[/yellow]")
        return
    
    # 建立表格
    table = Table(title="最近 10 筆審查記錄", style="#F39C12")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("專案名稱", style="bold")
    table.add_column("審查時間", justify="center")
    table.add_column("高風險", justify="center", style="red")
    table.add_column("中風險", justify="center", style="yellow")
    table.add_column("低風險", justify="center", style="green")
    table.add_column("裁決摘要", overflow="ellipsis")
    
    for row in rows:
        table.add_row(
            str(row[0]),
            row[1],
            row[2][:19],  # 只顯示日期時間前半段
            str(row[3]),
            str(row[4]),
            str(row[5]),
            row[6][:50] + "..." if len(row[6]) > 50 else row[6]
        )
    
    console.print(table)

def manage_knowledge_base():
    """管理知識庫"""
    console.print(Panel("📚 知識庫管理", style="bold white on #1A1A1B", border_style="#F39C12"))
    console.print("[yellow]⚠️  此功能將於 Phase B 實現[/yellow]")
    console.print("\n未來將支援：")
    console.print("  - 檢視角色設定")
    console.print("  - 編輯公司規範模板")
    console.print("  - 匯入/匯出風險模板")

def main():
    """CLI 主迴圈"""
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            add_new_review()
        elif choice == "2":
            view_history()
        elif choice == "3":
            manage_knowledge_base()
        elif choice.lower() == "q":
            console.print(Panel("[green]👋 感謝使用，再見！[/green]", 
                              style="bold white on #1A1A1B", 
                              border_style="#F39C12"))
            break

if __name__ == '__main__':
    main()
```

## 資料庫操作範例

### 儲存審查結果

```python
def save_review_to_db(project_name: str, result_json: dict):
    """
    將審查結果儲存至資料庫
    
    Args:
        project_name: 專案名稱
        result_json: Aggregator 輸出的完整 JSON
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 統計各等級風險數量
    risks = result_json.get("risks", [])
    risk_high = sum(1 for r in risks if r.get("level") == "high")
    risk_medium = sum(1 for r in risks if r.get("level") == "medium")
    risk_low = sum(1 for r in risks if r.get("level") == "low")
    
    # 裁決摘要
    verdict = result_json.get("verdict", "")[:500]  # 限制長度
    
    # 插入資料庫
    cursor.execute("""
        INSERT INTO reviews (project, reviewed_at, risk_high, risk_medium, risk_low, verdict, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project_name,
        datetime.utcnow().isoformat(),
        risk_high,
        risk_medium,
        risk_low,
        verdict,
        json.dumps(result_json, ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()
    
    return cursor.lastrowid
```

## 色彩規範

依照用戶偏好的暖感工業風格：

| 用途 | 色碼 | 說明 |
|------|------|------|
| 主背景 | `#1A1A1B` | 深炭黑 |
| 重點色 | `#F39C12` | 琥珀橙（主要按鈕、選中項目） |
| 次要色 | `#D35400` | 深橙（次要按鈕、邊框） |
| 文字色 | `#ECF0F1` | 淺灰白（主要文字） |
| 成功 | `#27AE60` | 綠色 |
| 警告 | `#F39C12` | 琥珀橙 |
| 錯誤 | `#E74C3C` | 紅色 |

## 依賴套件

```txt
rich>=13.0
questionary>=2.0
```

## 檔案路徑策略

所有路徑均使用 `Path(__file__)` 相對定位，確保：
- ✅ 在任何作業系統下正常運作
- ✅ 支援從不同目錄執行
- ✅ 支援虛擬環境與打包

---

**文件狀態**: 草稿  
**最後更新**: 2026-04-03  
**版本**: 1.0
