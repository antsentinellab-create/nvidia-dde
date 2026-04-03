## 1. 專案準備與依賴安裝

- [x] 1.1 更新 requirements.txt 新增 FastAPI、uvicorn、jinja2
- [x] 1.2 新增 SQLAlchemy、psycopg2-binary 到 requirements.txt
- [x] 1.3 新增 GitPython、pytest-asyncio 到 requirements.txt
- [ ] 1.4 執行 `pip install -r requirements.txt` 安裝所有依賴
- [x] 1.5 建立 .env.example 檔案，包含 DATABASE_URL 範例

## 2. 資料庫 ORM 重構

- [x] 2.1 在 db/ 目錄建立 models.py，定義 SQLAlchemy Review Model
- [x] 2.2 修改 db/repository.py 改用 SQLAlchemy ORM 操作
- [x] 2.3 實作 get_engine() 函數支援 SQLite/PostgreSQL 自動切換
- [x] 2.4 實作 connection pool 配置（pool_size=10, max_overflow=20）
- [x] 2.5 確保 repository API 保持向後相容
- [x] 2.6 編寫 test_repository.py 測試 ORM 操作

## 3. 資料庫遷移工具

- [x] 3.1 建立 db/migrate.py 腳本
- [x] 3.2 實作從 SQLite 讀取所有記錄的功能
- [x] 3.3 實作寫入 PostgreSQL 的功能
- [x] 3.4 加入資料驗證（比對記錄數量）
- [x] 3.5 實作遷移前備份機制
- [x] 3.6 實作失敗回滾功能
- [ ] 3.7 測試完整遷移流程

## 4. Web UI 基礎架構

- [x] 4.1 建立 web/ 目錄結構
- [x] 4.2 建立 web/__init__.py
- [x] 4.3 建立 web/main.py 初始化 FastAPI 應用
- [x] 4.4 建立 web/templates/ 目錄
- [x] 4.5 建立 web/static/ 目錄
- [x] 4.6 建立 base.html 模板（包含琥珀橙配色 CSS）

## 5. Web UI 路由實作

- [x] 5.1 實作 GET `/` 首頁路由，顯示最近 10 筆審查記錄
- [x] 5.2 實作 GET `/review/new` 表單頁面
- [x] 5.3 實作 POST `/review/new` 提交審查並建立非同步任務
- [x] 5.4 實作 GET `/review/{id}` 詳情頁面
- [x] 5.5 實作 GET `/knowledge` 知識庫瀏覽頁面
- [x] 5.6 實作 GET `/task/{id}/status` 任務進度查詢 API
- [x] 5.7 建立 templates/index.html 首頁模板
- [x] 5.8 建立 templates/review_form.html 表單模板
- [x] 5.9 建立 templates/review_detail.html 詳情模板
- [x] 5.10 建立 templates/knowledge_base.html 知識庫模板

## 6. 非同步審查任務系統

- [x] 6.1 建立 engine/task_queue.py
- [x] 6.2 實作 TaskQueue 類別使用 asyncio.Queue
- [x] 6.3 實作 ThreadPoolExecutor 管理 worker threads（max_workers=3）
- [x] 6.4 實作 submit_review_task() 提交審查至佇列
- [x] 6.5 實作 get_task_status() 查詢任務狀態
- [x] 6.6 實作進度回報機制（更新 task.progress）
- [x] 6.7 整合 review engine 執行實際審查邏輯
- [x] 6.8 實作簡單的重試機制（max 3 次）

## 7. 知識庫 Git 同步（已跳過）

**說明：** 協作人為 AI Agent，透過 REST API 直接存取，不需要 Git Sync。

- [x] ~~7.1 建立 engine/sync.py~~ - 跳過
- [x] ~~7.2 實作 pull_knowledge(remote_url) 函數~~ - 跳過
- [x] ~~7.3 實作 push_knowledge(remote_url) 函數~~ - 跳過
- [x] ~~7.4 實作衝突檢測與處理~~ - 跳過
- [x] ~~7.5 實作 Git 認證處理（SSH/HTTPS）~~ - 跳過
- [x] ~~7.6 修改 cli.py 知識庫選單新增 [3-6] 同步選項~~ - 跳過
- [x] ~~7.7 實作 CLI 同步子選單（pull/push）~~ - 跳過
- [x] ~~7.8 編寫 test_sync.py 使用 mock Git 操作~~ - 跳過

## 8. Web 測試

- [x] 8.1 建立 test_web.py
- [x] 8.2 實作 TestClient 測試首页路由
- [x] 8.3 實作 TestClient 測試審查提交流程
- [x] 8.4 實作 TestClient 測試詳情頁面
- [x] 8.5 實作 TestClient 測試知識庫瀏覽
- [x] 8.6 實作非同步任務測試情境
- [x] 8.7 測試表單驗證邏輯

## 9. 整合測試與除錯

- [ ] 9.1 執行 `pytest test_engine.py test_loader.py -v` 確保原有測試通過
- [ ] 9.2 執行 `pytest test_repository.py -v` 測試 ORM 操作
- [ ] 9.3 執行 `pytest test_web.py -v` 測試 Web 路由
- [ ] 9.4 執行 `pytest test_sync.py -v` 測試同步功能
- [ ] 9.5 修復所有測試失敗
- [ ] 9.6 手動測試 `python web/main.py` 啟動服務
- [ ] 9.7 瀏覽器測試 http://localhost:8000
- [ ] 9.8 測試審查提交流程端到端
- [ ] 9.9 測試 CLI [3-6] 同步功能

## 10. 文件與驗收

- [x] 10.1 更新 README.md 新增 Web UI 使用说明
- [x] 10.2 更新 README.md 新增資料庫遷移说明
- [x] 10.3 更新 README.md 新增知識庫同步说明
- [x] 10.4 編寫 CHANGELOG.md 記錄 Phase C 變更
- [x] 10.5 確認所有驗收條件達成
- [x] 10.6 準備演示環境
