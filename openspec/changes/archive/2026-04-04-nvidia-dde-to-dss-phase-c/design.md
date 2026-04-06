## Context

**背景：**
DSS 在 Phase A/B 已完成基礎審查引擎與 CLI 介面，使用 SQLite 單機資料庫與本地知識庫。隨著工程部門需要多人協作能力，必須升級為支援並發訪問、Web 視覺化、以及知識庫共享的部門級平台。

**現況：**
- CLI 完整運作但僅限單人使用
- SQLite history.db 不支援並發寫入
- knowledge/ 目錄無法團隊共享
- 無 Web 介面

**限制條件：**
- 保持 CLI 向後相容
- 不引入中央伺服器（Phase D 才做認證）
- 測試覆蓋率不退步
- 預算：開發時程 2-3 週

**利害關係人：**
- 工程部門開發人員（主要使用者）
- 系統維護團隊（運維）
- 技術負責人（架構審核）

## Goals / Non-Goals

**Goals:**
- 實作 FastAPI Web UI 提供可視化操作介面
- 遷移至 PostgreSQL 支援多人並發寫入
- 建立 Git 基礎的知識庫同步機制
- 實作非同步審查任務執行
- 維持 100% CLI 向後相容
- 測試覆蓋率維持或提升

**Non-Goals:**
- 使用者認證與登入機制（Phase D）
- RBAC 權限控制（Phase D）
- Docker 容器化與部署設定（Phase D）
- 修改 Aggregator 裁決邏輯
- 取代 CLI 介面

## Decisions

### 1. Web 框架選擇：FastAPI + Jinja2 vs FastAPI + React

**決策：FastAPI + Jinja2**

**理由：**
- 輕量級，減少前端建構複雜度
- 伺服器端渲染適合內部工具
- 快速原型開發，維護簡單
- React 會增加 build step 與部署複雜度，對本階段過於重量級

**替代方案考慮：**
- FastAPI + React: 適合大型 C 端產品，但增加不必要的複雜度
- Flask: 非同步支援較弱，不利於背景任務
- Django: 過於重量級，學習曲線陡峭

### 2. 資料庫遷移策略：Big Bang vs 漸進式

**決策：Big Bang 一次性遷移**

**理由：**
- 現有資料量小（history.db 僅數 MB）
- 單一開發者資料，無複雜業務邏輯
- 漸進式需要同步機制，增加不必要的複雜度
- 提供完整回滾機制降低風險

**替代方案考慮：**
- 漸進式遷移：適合大型生產系統，但本案例過度設計
- 雙寫模式：增加程式碼複雜度，無實質效益

### 3. 非同步任務：Celery vs ThreadPoolExecutor

**決策：ThreadPoolExecutor + asyncio.Queue**

**理由：**
- 輕量級，無需額外基礎設施（Redis/RabbitMQ）
- 適合中小型並發量（max_workers=3）
- 與 FastAPI asyncio 原生整合
- Celery 學習曲線陡峭，需要額外訊息佇列

**替代方案考慮：**
- Celery: 適合大型分散式系統，但需要 Redis/RabbitMQ
- RQ (Redis Queue): 依賴 Redis，增加基礎設施負擔
- FastAPI BackgroundTasks: 功能陽春，無法追蹤進度

### 4. 知識庫同步：Git 原生命令 vs GitPython

**決策：GitPython 函式庫**

**理由：**
- Python 原生 API，易於整合與測試
- 跨平台相容性佳
- 錯誤處理比 subprocess 更優雅
- Mock 測試容易實作

**替代方案考慮：**
- subprocess + git commands: 依賴系統命令，錯誤處理複雜
- PyGit2: libgit2 綁定，編譯安裝複雜

### 5. ORM 抽象層：SQLAlchemy Core vs SQLAlchemy ORM

**決策：SQLAlchemy ORM with Declarative Base**

**理由：**
- 型別安全，支援 mypy
- 物件導向操作更直觀
- 自動產生 schema
- 未來若需更換資料庫更容易

**替代方案考慮：**
- SQLAlchemy Core: 更接近 SQL，但缺少 ORM 便利性
- Peewee: 輕量但功能較少
- Tortoise ORM: 非同步 ORM，但生態系較小

### 6. 專案結構：Monolithic vs Modular

**決策：Modular 模組化結構**

```
web/
├── __init__.py
├── main.py          # FastAPI app
├── routes.py        # URL routing
├── templates/       # Jinja2 templates
└── static/         # CSS/JS assets
```

**理由：**
- 職責分離清晰
- 易於測試（可單獨測試 routes）
- 符合 FastAPI 最佳實踐

## Risks / Trade-offs

### [Risk] PostgreSQL 並發衝突
**→ Mitigation:** 
- 使用 SQLAlchemy session 隔離級別
- 實作 optimistic locking（version column）
- 測試套件包含並發測試情境

### [Risk] Git 同步衝突
**→ Mitigation:**
- pull 時檢測衝突立即中止
- 要求使用者手動解決衝突
- 提供冲突文件清單

### [Risk] 非同步任務失敗無重試
**→ Mitigation:**
- 實作簡單的 retry 機制（max 3 次）
- 失敗任務記錄完整 stack trace
- 提供管理員查看錯誤日誌

### [Risk] 資料庫遷移失敗
**→ Mitigation:**
- 遷移前完整備份 SQLite
- 驗證記錄數量一致
- 提供一鍵回滾腳本

### [Trade-off] 放棄 Celery 換取簡單性
- **Gain:** 減少基礎設施依賴，快速上線
- **Lose:** 缺少分散式任務排程能力（Phase D 再評估）

### [Trade-off] 使用 Jinja2 而非 React
- **Gain:** 快速開發，零前端建構
- **Lose:** 使用者體驗較不流暢（可接受）

## Migration Plan

### 階段 1: 資料庫遷移 (Day 1-2)
1. 新增 requirements: `sqlalchemy`, `psycopg2-binary`
2. 重構 `db/repository.py` 使用 SQLAlchemy ORM
3. 建立 `db/migrate.py` 遷移腳本
4. 測試 SQLite fallback 機制

### 階段 2: Web UI 開發 (Day 3-7)
1. 初始化 FastAPI 專案結構
2. 實作路由：`/`, `/review/new`, `/review/{id}`, `/knowledge`
3. 建立 Jinja2 模板
4. 整合非同步審查任務
5. 實作 WebSocket 或 polling 顯示進度

### 階段 3: 知識庫同步 (Day 8-9)
1. 新增 `engine/sync.py`
2. 實作 `pull_knowledge()` / `push_knowledge()`
3. CLI 新增 [3-6] 選單
4. 測試 Git 操作流程

### 階段 4: 測試與驗收 (Day 10-12)
1. 編寫 `test_repository.py`
2. 編寫 `test_web.py`
3. 編寫 `test_sync.py`
4. 執行完整測試套件
5. 修復 bug 與效能優化

### 階段 5: 文件與部署準備 (Day 13-14)
1. 更新 README.md
2. 編寫 `.env.example`
3. 準備演示環境
4. 驗收測試

**回滾策略：**
- 若 Web UI 嚴重失敗：停用 web service，CLI 仍可運作
- 若資料庫遷移失敗：恢復 SQLite backup
- 若知識庫同步失敗：切換回本地模式

## Open Questions

1. **PostgreSQL 託管方案？**
   - 選項：本地安裝 vs Docker vs 雲端 (Supabase/Neon)
   - 建議：開發期本地 Docker，生產期雲端

2. **最大並發用戶數？**
   - 取決於 connection pool size (預設 10)
   - 需要根據實際負載調整

3. **知識庫遠端倉庫位置？**
   - 選項：GitHub private repo vs GitLab vs 內部 Git server
   - 需與團隊協調

4. **非同步任務持久化？**
   - 目前：記憶體佇列（重啟後遺失）
   - 未來：可考慮持久化至資料庫（Phase D）
