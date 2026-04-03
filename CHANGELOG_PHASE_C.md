# DSS Phase C - 變更日誌

## [3.0.0] - 2026-04-03

### 🎉 重大升級：從單人工具到部門級平台

#### ✨ 新增功能

**1. Web UI 介面**
- FastAPI + Jinja2 輕量網頁介面
- 琥珀橙工業風格視覺設計（深炭黑 #1A1A1B + 琥珀橙 #F39C12）
- 主要頁面：
  - `/` 首頁：顯示最近審查記錄
  - `/review/new` 提交新審查表單
  - `/review/{id}` 審查詳情與 JSON 視覺化
  - `/knowledge` 知識庫瀏覽（唯讀）
- 響應式設計，支援手機與桌面

**2. 資料庫升級**
- SQLAlchemy ORM 抽象層
- 支援 SQLite 與 PostgreSQL 雙後端
- 環境變數 `DATABASE_URL` 控制連接
- 自動 connection pooling（pool_size=10, max_overflow=20）
- 向後相容：預設使用 SQLite

**3. 非同步審查任務系統**
- ThreadPoolExecutor + asyncio.Queue
- 可配置並發 worker 數量（預設 3）
- 即時進度追蹤（0-100%）
- 5 階段審查狀態顯示
- REST API `/task/{id}/status` 查詢進度
- JavaScript polling 每 2 秒自動更新

**4. 資料庫遷移工具**
- `db/migrate.py` 一鍵遷移 SQLite → PostgreSQL
- 自動備份與回滾機制
- 資料完整性驗證
- 零停機遷移支援

#### 🔧 技術棧升級

**新增依賴：**
- `fastapi==0.109.0` - Web 框架
- `uvicorn[standard]==0.27.0` - ASGI server
- `jinja2==3.1.3` - 模板引擎
- `sqlalchemy==2.0.25` - ORM
- `psycopg2-binary==2.9.10` - PostgreSQL 驅動
- `python-dotenv==1.0.0` - 環境變數管理
- `pytest-asyncio==0.23.3` - 非同步測試

**檔案結構擴充：**
```
web/                    # 新增 Web UI 模組
├── main.py            # FastAPI 應用
├── templates/         # Jinja2 模板
│   ├── base.html
│   ├── index.html
│   ├── review_form.html
│   ├── review_detail.html
│   ├── knowledge_base.html
│   └── ...
└── static/css/        # CSS 樣式
    └── style.css

engine/
└── task_queue.py      # 非同步任務系統（新增）

db/
├── models.py          # SQLAlchemy ORM models（新增）
├── repository.py      # 重構為 ORM 版本
└── migrate.py         # 遷移工具（新增）

test_web.py            # Web 測試（新增）
test_repository.py     # ORM 測試（新增）
```

#### 📊 測試覆蓋率

- **ORM 測試**: 15 個測試情境
- **Web 測試**: 18 個測試情境
- **整合測試**: 涵蓋非同步任務、API、靜態文件
- 維持 100% 向後相容性測試

#### 🚀 使用方式

**啟動 Web UI:**
```bash
source .venv/bin/activate
python web/main.py
# 訪問 http://localhost:8000
```

**資料庫遷移:**
```bash
# 1. 在 .env 設置 PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/dss_db

# 2. 執行遷移
python db/migrate.py
```

**執行測試:**
```bash
pytest test_engine.py test_loader.py test_repository.py test_web.py -v
```

#### ⚠️ 重要變更

- **CLI 完全保留**：所有原有功能正常運作
- **SQLite fallback**：若無 PostgreSQL 環境自動降級
- **知識庫共享**：暫緩 Git Sync（Phase D 再評估）

#### 📝 已知問題

- 非同步任務重啟後佇列會清空（記憶體儲存）
- 知識庫僅支援本地瀏覽（無 Git 同步）
- 無使用者認證（所有人共用）

#### 🔮 未來計劃 (Phase D)

- 使用者認證與登入機制
- RBAC 權限控制
- Docker 容器化部署
- 知識庫 Git 同步（若需要）

---

**向 Phase B 致敬** 🙏  
感謝打下堅實的 CLI 基礎，讓 Phase C 能順利擴展為完整平台！
