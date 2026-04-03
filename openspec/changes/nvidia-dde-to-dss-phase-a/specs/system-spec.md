# 系統規格說明書

## 概述

Design Review Support System (DSS) Phase A - 將 Design Decision Engine 升級為完整的審查支援系統。

## 核心功能

### 1. 知識庫系統

**位置**: `knowledge/`

#### 角色設定 (`knowledge/roles/`)
- `risk_analyst.json` - Risk-Analyst 角色定義
- `completeness_reviewer.json` - Completeness-Reviewer 角色定義
- `improvement_advisor.json` - Improvement-Advisor 角色定義
- `aggregator.json` - Aggregator 角色定義

**格式**:
```json
{
  "id": "model-id",
  "name": "角色名稱",
  "system": "系統提示詞",
  "focus_fields": ["主責欄位"],
  "focus_desc": "職責描述"
}
```

#### 預留目錄
- `knowledge/standards/` - 未來存放公司規範模板
- `knowledge/risk_templates/` - 未來存放風險模板

### 2. 資料庫模組

**位置**: `db/`

#### Schema (`db/schema.sql`)
```sql
CREATE TABLE reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    risk_high   INTEGER DEFAULT 0,
    risk_medium INTEGER DEFAULT 0,
    risk_low    INTEGER DEFAULT 0,
    verdict     TEXT,
    result_json TEXT NOT NULL
);
```

#### 初始化腳本 (`db/init_db.py`)
- 執行一次建立 `db/history.db`
- 建立索引加速查詢
- 建立觸發程序自動更新時間戳

### 3. 載入模組

**位置**: `engine/`

#### Loader (`engine/loader.py`)
- `get_knowledge_base_path()` - 取得 knowledge/ 路徑
- `load_role(filename)` - 載入單個角色檔案
- `load_roles()` - 載入所有角色
- Fallback 機制：載入失敗時使用內建值

### 4. 互動式 CLI

**位置**: `cli.py`

#### 選單功能
1. **新增審查** - 執行新的設計審查
2. **查歷史記錄** - 查看最近 10 筆記錄
3. **管理知識庫** - 知識庫管理（Phase A 預覽）
4. **退出系統** - 離開 CLI

#### 視覺風格
- **主背景**: #1A1A1B (深炭黑)
- **重點色**: #F39C12 (琥珀橙)
- **次要色**: #D35400 (深橙)
- **框架**: Rich Panel + Table
- **選單**: Questionary Select

### 5. 審查流程整合

#### run_design_review(spec) -> dict
- 呼叫三位專家進行審查
- 合併結果並送交 Aggregator
- 回傳完整 JSON 結果
- 包含錯誤處理與 fallback

#### save_review_to_db(project_name, result_json)
- 統計各等級風險數量
- 寫入 SQLite 資料庫
- 儲存完整 JSON 供詳細查詢

## 技術棧

| 項目 | 版本 | 用途 |
|------|------|------|
| Python | 3.13.5 | 主要語言 |
| openai | 2.30.0 | NVIDIA API 客戶端 |
| pytest | 9.0.2 | 單元測試 |
| rich | >=13.0 | CLI 美化 |
| questionary | >=2.0 | 互動選單 |
| sqlite3 | 內建 | 資料庫 |

## 檔案結構

```
.
├── cli.py                          # 互動式 CLI 入口
├── design_decision_engine.py       # 核心引擎（保持不變）
├── test_engine.py                  # 單元測試
├── README.md                       # 使用手冊
├── CLI_USAGE.md                    # CLI 使用指南
├── requirements.txt                # 依賴清單
├── start.sh                        # 快速啟動腳本
├── engine/
│   ├── __init__.py
│   └── loader.py                   # 知識庫載入模組
├── db/
│   ├── schema.sql                  # 資料庫結構
│   ├── init_db.py                  # 資料庫初始化
│   └── history.db                  # 審查歷史資料庫
└── knowledge/
    ├── roles/                      # 專家角色設定
    │   ├── risk_analyst.json
    │   ├── completeness_reviewer.json
    │   ├── improvement_advisor.json
    │   └── aggregator.json
    ├── standards/                  # 公司規範（預留）
    │   └── .gitkeep
    └── risk_templates/             # 風險模板（預留）
        └── .gitkeep
```

## 驗收標準

### ✅ 已達成

1. **pytest test_engine.py -v** 全綠（5/5 passed）
2. **python db/init_db.py** 成功建立 db/history.db
3. **python cli.py** 能顯示主選單
4. **選 [1]** 能觸發審查流程並寫入 DB
5. **選 [2]** 能列出歷史記錄
6. **不修改** design_decision_engine.py 任何現有函數
7. **ROLES 完全抽離**至 knowledge/roles/*.json
8. **新增依賴僅** rich + questionary

## 使用方式

### 快速啟動

```bash
export NVIDIA_API_KEY="nvapi-YOUR_KEY"
./start.sh
```

### 手動啟動

```bash
source .venv/bin/activate
python cli.py
```

## 未來擴展（Phase B+）

### Phase B: 知識庫豐富化
- 填充 standards/ 與公司規範
- 填充 risk_templates/ 與風險模式
- 建立搜尋與推薦機制

### Phase C: Web 介面
- Flask/FastAPI 後端
- React/Vue 前端
- 視覺化儀表板

### Phase D: 進階功能
- 多專案管理
- 團隊協作
- AI 模型自動切換
- 報告匯出（PDF/Markdown）

---

**版本**: v1.1.0  
**日期**: 2026-04-03  
**狀態**: ✅ 完成
