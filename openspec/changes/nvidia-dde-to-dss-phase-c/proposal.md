## Why

隨著 DSS 在 Phase A/B 完成基礎審查引擎與 CLI 介面後，已驗證其作為單人工具的價值。然而，工程部門需要將其升級為多人協作平台，以支援團隊共用知識庫、Web 視覺化介面、以及並發訪問能力。此變革將使 DSS 從個人效率工具轉型為部門級基礎設施。

## What Changes

- **新增 Web UI**：FastAPI + Jinja2 輕量網頁介面，提供可視化審查入口
- **資料庫遷移**：從 SQLite 升級至 PostgreSQL，支援多人並發寫入
- **知識庫共享機制**：透過 Git 版本控制實現遠端同步，不引入中央伺服器
- **非同步審查任務**：Web 提交後台執行，避免阻塞請求
- **CLI 功能擴充**：新增知識庫同步選單 [3-6]
- **新增測試覆蓋**：Repository ORM 測試、Web 路由測試、Git Sync 測試

## Capabilities

### New Capabilities
- `web-ui`: FastAPI Web 介面，含首頁、審查提交、詳情查看、知識庫瀏覽頁面
- `postgresql-support`: PostgreSQL 資料庫支援與 SQLAlchemy ORM 抽象層
- `knowledge-sync`: 知識庫 Git 同步機制，支援 pull/push 遠端倉庫
- `async-review-tasks`: 背景非同步執行審查任務
- `database-migration`: SQLite 至 PostgreSQL 的資料遷移工具

### Modified Capabilities
- `cli-interface`: CLI 知識庫選單擴充，新增 [3-6] 同步功能（向後相容）
- `repository-layer`: repository.py 改用 SQLAlchemy ORM，保留 SQLite fallback

## Impact

- **程式碼影響**：
  - 新增 `web/` 目錄（FastAPI 應用）
  - 修改 `db/repository.py`（ORM 重構）
  - 新增 `db/migrate.py`（遷移腳本）
  - 新增 `engine/sync.py`（Git 同步邏輯）
  - 修改 `cli.py`（新增子選單）
  
- **依賴新增**：
  - `fastapi`、`uvicorn`、`jinja2`（Web 框架）
  - `sqlalchemy`、`psycopg2-binary`（資料庫 ORM）
  - `gitpython`（Git 操作）
  - `pytest-asyncio`（非同步測試）
  
- **資料庫影響**：
  - 現有 `history.db` 需遷移至 PostgreSQL
  - 環境變數 `DATABASE_URL` 控制資料庫連接
  
- **向後相容**：
  - CLI 完整保留，Web 為新增入口
  - SQLite fallback 確保單機環境仍可運作
