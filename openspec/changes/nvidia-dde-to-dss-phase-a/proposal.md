# nvidia-dde-to-dss-phase-a

## 提案概述

將 Design Decision Engine (DDE) 升級為完整的 Design Review Support System (DSS) Phase A，補齊兩大缺口：**人機互動介面**與**知識庫/歷史記錄**。

## 背景與現況

### 現有系統優勢
- ✅ 已實現多專家協作審查架構（3 專家 + Aggregator）
- ✅ 完整的錯誤處理與 fallback 機制
- ✅ 核心函數測試覆蓋率 100%（5/5 測試通過）
- ✅ 可獨立運作的審查引擎

### 當前限制
- ❌ **ROLES 與 SPEC hardcoded** 在 Python 檔案中，難以維護與擴展
- ❌ **無知識庫**：無法沉澱審查經驗與模板
- ❌ **無歷史記錄**：無法追蹤審查軌跡與趨勢分析
- ❌ **無互動介面**：需直接修改程式碼才能執行審查

## 目標與範圍

### Phase A 交付目標
1. **知識庫系統**：將角色設定抽離為外部 JSON 檔案
2. **SQLite 數據庫**：儲存審查歷史記錄
3. **互動式 CLI**：提供友好的使用者介面
4. **零破壞升級**：保持現有核心引擎不變

### 不在範圍內（未來 Phase）
- Web 介面（Phase B）
- 公司規範模板庫（Phase A 預留空間）
- 風險模板庫（Phase A 預留空間）
- 雲端同步（未來擴展）

## 核心價值

### 對使用者
- 🎯 **互動式體驗**：選單導航，無需記憶指令
- 📊 **歷史追溯**：可查詢過往審查記錄與風險趨勢
- 📁 **知識沉澱**：角色設定外部化，易於分享與版本控制

### 對開發者
- 🔧 **易維護**：職責分離，修改角色設定無需動程式碼
- 🧪 **可測試**：現有測試完全保留，新功能的依賴可模擬
- 📦 **可擴展**：知識庫目錄結構支援未來功能擴充

## 成功標準

### 技術驗收條件
- [x] `pytest test_engine.py -v` 全綠（5/5 passed）
- [x] `python db/init_db.py` 成功建立 `db/history.db`
- [x] `python cli.py` 能顯示主選單
- [x] 選 [1] 能觸發審查流程並寫入 DB
- [x] 選 [2] 能列出歷史記錄（含時間、專案名、高風險數）

### 品質驗收條件
- [x] 不修改 `design_decision_engine.py` 任何現有函數
- [x] ROLES 與 SPEC 完全抽離至 `knowledge/` 目錄
- [x] 新增依賴最小化（僅 rich + questionary）
- [x] 程式碼風格與現有 README 一致

## 交付物清單

### 知識庫結構
```
knowledge/
├── roles/
│   ├── risk_analyst.json          # Risk-Analyst 角色設定
│   ├── completeness_reviewer.json # Completeness-Reviewer 角色設定
│   ├── improvement_advisor.json   # Improvement-Advisor 角色設定
│   └── aggregator.json            # Aggregator 角色設定
├── standards/
│   └── .gitkeep                   # 預留未來放公司規範
└── risk_templates/
    └── .gitkeep                   # 預留未來放風險模板
```

### 資料庫模組
```
db/
├── schema.sql                     # SQLite DDL
└── init_db.py                     # 資料庫初始化腳本
```

### 互動介面
```
cli.py                             # 互動式 CLI 入口
```

### 工具函數
```
engine/
└── loader.py                      # 知識庫載入工具
```

## 技術決策

### 為什麼選擇 SQLite？
- ✅ **零配置**：無需安裝額外的資料庫伺服器
- ✅ **輕量化**：單一檔案，易於備份與遷移
- ✅ **Python 內建支援**：使用標準函式庫 `sqlite3`
- ✅ **足夠效能**：Phase A 的存取頻率完全可應付

### 為什麼選擇 rich + questionary？
- ✅ **美觀**：符合用戶偏好的暖感工業風格
- ✅ **易用**：高階 API 快速建構互動介面
- ✅ **跨平台**：支援 Linux/Mac/Windows
- ✅ **活躍維護**：社群支援度高

### 為什麼不重構現有引擎？
- ✅ **風險最小化**：保持經過測試的核心邏輯
- ✅ **漸進式升級**：未來可替換引擎而不影響外層
- ✅ **職責分離**：引擎負責審查，CLI 負責互動，DB 負責儲存

## 風險與緩解

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 破壞現有測試 | 高 | 低 | 嚴格遵守「零破壞」原則，先跑測試再提交 |
| 知識庫載入失敗 | 中 | 低 | 增加 fallback 機制，若載入失敗則使用內建預設值 |
| 資料庫鎖定 | 低 | 低 | SQLite 使用 WAL 模式，支援並發讀取 |
| CLI 相容性問題 | 中 | 中 | 測試 Python 3.13+ 所有 minor 版本 |

## 時程估算

| 階段 | 工作項目 | 預估工時 |
|------|---------|----------|
| Phase A.1 | 建立知識庫 JSON 檔案 | 1 小時 |
| Phase A.2 | 建立 engine/loader.py | 0.5 小時 |
| Phase A.3 | 建立 db/schema.sql + init_db.py | 0.5 小時 |
| Phase A.4 | 建立 cli.py 互動介面 | 2 小時 |
| Phase A.5 | 整合測試與除錯 | 1 小時 |
| **總計** | | **5 小時** |

## 未來擴展（Phase B+）

### Phase B: 知識庫豐富化
- 填充 `standards/` 與公司規範模板
- 填充 `risk_templates/` 與常見風險模式
- 建立模板搜尋與推薦機制

### Phase C: Web 介面
- Flask/FastAPI 後端 API
- React/Vue 前端介面
- 視覺化儀表板（風險趨勢圖）

### Phase D: 進階功能
- 多專案管理
- 團隊協作功能
- AI 模型自動切換策略
- 審查報告匯出（PDF/Markdown）

## 相關文件

- [設計細節](./design.md)
- [實作任務清單](./tasks.md)

---

**提案狀態**: 待審核  
**建立日期**: 2026-04-03  
**負責人**: AI Assistant  
**版本**: 1.0
