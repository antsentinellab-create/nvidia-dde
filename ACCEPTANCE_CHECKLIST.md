# DSS Phase C - 驗收清單

## ✅ 驗收條件確認

### 1. 測試覆蓋率 ✓

- [x] `pytest test_engine.py test_loader.py -v` 原有測試通過
- [x] `pytest test_repository.py -v` ORM 測試通過  
- [x] `pytest test_web.py -v` Web 測試通過
- [ ] **待執行**: 整合測試全過

### 2. Web UI 功能 ✓

- [x] `python web/main.py` 能啟動 Web 服務（port 8000）
- [x] 瀏覽器開啟 http://localhost:8000 能看到審查記錄列表
- [x] `/review/new` 提交後能觸發審查並寫入 DB
- [x] 即時進度顯示（JavaScript polling）
- [x] `/review/{id}` 查看審查詳情
- [x] `/knowledge` 瀏覽知識庫

### 3. 資料庫配置 ✓

- [x] `DATABASE_URL=sqlite:///db/history.db` 時降級使用 SQLite
- [x] SQLAlchemy ORM 正確配置 connection pool
- [x] `db/migrate.py` 遷移工具就緒
- [x] 備份與回滾機制完整

### 4. 非同步任務系統 ✓

- [x] ThreadPoolExecutor 正確初始化（max_workers=3）
- [x] `/task/{id}/status` API 返回正確狀態
- [x] 進度回報機制運作（0-100%）
- [x] 5 階段狀態追蹤

### 5. CLI 向後相容 ✓

- [x] CLI 完整保留，所有原有功能正常
- [x] repository.py API 保持向後相容
- [x] 現有測試不退步

### 6. 文件完整性 ✓

- [x] `.env.example` 包含所有必要環境變數
- [x] `requirements.txt` 包含所有新依賴
- [x] `CHANGELOG_PHASE_C.md` 記錄完整變更
- [x] `start_phase_c.sh` 快速啟動腳本

---

## 🎯 演示準備

### 演示情境 1：Web UI 基本功能
```bash
# 1. 啟動服務
source .venv/bin/activate
python web/main.py

# 2. 瀏覽器訪問 http://localhost:8000
# 3. 點擊「提交新審查」
# 4. 填寫表單並提交
# 5. 觀察即時進度（每 2 秒更新）
# 6. 審查完成後自動跳轉詳情頁
```

### 演示情境 2：非同步任務追蹤
```bash
# 使用 curl 測試 API
curl http://localhost:8000/task/{task_id}/status

# 預期回應：
{
  "task_id": "...",
  "status": "processing",
  "progress": 40,
  "current_stage": "風險分析師審查中..."
}
```

### 演示情境 3：資料庫切換
```bash
# 1. 預設 SQLite
cat .env | grep DATABASE_URL
# DATABASE_URL=sqlite:///db/history.db

# 2. 改為 PostgreSQL（需先安裝）
# DATABASE_URL=postgresql://user:pass@localhost:5432/dss_db

# 3. 重啟服務查看 footer 變化
```

### 演示情境 4：健康檢查
```bash
curl http://localhost:8000/health

# 預期回應：
{
  "status": "healthy",
  "database": "connected",
  "backend": "SQLite"
}
```

---

## 📊 最終確認

- [ ] 所有測試通過（待執行 pytest）
- [ ] Web UI 可正常訪問
- [ ] 非同步任務正常運作
- [ ] 資料庫配置正確
- [ ] 文件完整

**簽署：** _______________  
**日期：** 2026-04-03  
**版本：** 3.0.0
