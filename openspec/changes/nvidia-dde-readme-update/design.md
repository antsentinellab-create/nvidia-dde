# nvidia-dde-readme-update - 設計細節

## 📍 更新位置總覽

| 章節 | 行號範圍（約） | 改動類型 |
|------|---------------|----------|
| 標題與概述 | L1-L15 | 修改 + 新增 |
| 系統架構 | L42-L82 | 新增圖示 |
| 技術棧 | L85-L100 | 新增表格列 |
| 安裝與設定 | L104-L126 | 替換指令 |
| 使用方式 | L128-L173 | 新增 CLI 章節 |
| 專案結構 | 新增章節 | 完整目錄樹 |
| 版本紀錄 | L486- | 新增 v1.1.0 |

## 🔧 詳細更新內容

### 1. 標題與概述 (L1-L15)

**原始內容**:
```markdown
# 設計決策引擎 (Design Decision Engine)

## 📋 專案概述

這是一個基於多專家協作的**系統設計審查引擎**...
```

**更新為**:
```markdown
# 設計決策支援系統 (Design Decision Support System)

## 📋 專案概述

這是一個基於多專家協作的**系統設計審查引擎**，利用多個 AI 模型模擬不同領域的資深架構師，對系統設計規格進行全方位審查與風險分析。

### 🎉 Phase A 升級亮點

從 v1.0.x 的 Design Decision Engine (DDE) 升級為完整的 **Design Review Support System (DSS)**，新增三大核心功能：

1. **🖥️ 互動式 CLI 介面** - 使用 rich + questionary 建構友善的選單介面
2. **📚 知識庫系統** - 將專家角色抽離為外部 JSON 設定檔，易於維護與擴展
3. **💾 SQLite 歷史記錄** - 儲存所有審查記錄，支援趨勢分析與回顧

### 核心概念

透過角色分工的方式，邀請三位不同專長的 AI 專家進行 Code Review：
- **Risk-Analyst**（風險分析師）：專注於安全性與風險識別
- **Completeness-Reviewer**（完整性審查員）：檢查需求覆蓋率
- **Improvement-Advisor**（改善顧問）：提供優化建議與亮點發現

最後由 **Aggregator**（總協調師）整合所有專家意見，生成最終裁決報告。
```

### 2. 系統架構 (L42-L82)

**在現有架構圖後新增**:

```markdown
### 🏗️ DSS 系統架構（v1.1.0）

```
┌─────────────────────────────────────────────────────────┐
│                    cli.py (互動式入口)                   │
│   [1] 新增審查  [2] 查歷史  [3] 知識庫  [Q] 退出         │
│              Rich + Questionary 美化介面                 │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  engine/      │  │  knowledge/   │  │  db/          │
│  loader.py    │  │  roles/       │  │  history.db   │
│  (載入模組)   │  │  standards/   │  │  (SQLite)     │
│  fallback 機制 │  │  risk_templates│ └───────────────┘
└───────┬───────┘  └───────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│        design_decision_engine.py (核心引擎)              │
│   ┌─────────────────────────────────────────────────┐   │
│   │ Risk-Analyst (DeepSeek-V3.2)                    │   │
│   │ Completeness-Reviewer (Qwen3.5-397B)            │   │
│   │ Improvement-Advisor (Mistral Large 2)           │   │
│   └─────────────────────────────────────────────────┘   │
│                    ↓ Aggregator                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │ Nemotron-Ultra 253B (最終裁決）                  │   │
│   └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**架構層次說明**:
1. **CLI 層** (`cli.py`) - 使用者互動介面
2. **支撐層** (`engine/`, `knowledge/`, `db/`) - 知識庫載入 + 歷史記錄
3. **引擎層** (`design_decision_engine.py`) - 多專家審查核心（保持不變）
```

### 3. 技術棧 (L85-L100)

**更新表格**:

```markdown
## 📦 技術棧

| 項目 | 版本/型號 | 用途 |
|------|----------|------|
| **Python** | 3.13.5 | 主要開發語言 |
| **openai** | 2.30.0 | NVIDIA API 客戶端 |
| **pytest** | 9.0.2 | 單元測試框架 |
| **rich** | >=13.0 | CLI 介面美化（暖感工業風格） |
| **questionary** | >=2.0 | 互動式選單 |

### 🤖 使用的 AI 模型
```

### 4. 安裝與設定 (L104-L126)

**完全替換**:

```markdown
## 🔧 安裝與設定

### 前置作業

```bash
# 1. 克隆或進入專案目錄
cd ~/Applications/NVIDIA

# 2. 建立虛擬環境（若尚未建立）
python3 -m venv .venv

# 3. 啟動虛擬環境
source .venv/bin/activate
```

### 安裝依賴套件

```bash
# 使用 requirements.txt 一次性安裝
pip install -r requirements.txt
```

**依賴清單**:
- `openai==2.30.0` - NVIDIA API 客戶端
- `pytest==9.0.2` - 單元測試框架
- `rich>=13.0` - CLI 介面美化
- `questionary>=2.0` - 互動式選單

### 初始化資料庫（首次執行）

```bash
# 建立 SQLite 資料庫與表格
python db/init_db.py
```

**預期輸出**:
```
📍 資料庫路徑：/path/to/db/history.db
📋 Schema 路徑：/path/to/db/schema.sql
✅ 資料庫初始化成功！
   檔案大小：24576 bytes
   建立表格：reviews, sqlite_sequence
   建立索引：idx_reviews_reviewed_at, idx_reviews_project, idx_reviews_risk_high
```

### API 金鑰設定
```

### 5. 使用方式 (L128-L173)

**新增章節並重新編號**:

```markdown
## 🚀 使用方式

### 🖥️ 互動式 CLI（推薦，v1.1.0+）

從 v1.1.0 開始，提供互動式 CLI 介面，更友善的使用體驗！

#### 方法一：快速啟動腳本

```bash
# 設定 API 金鑰
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"

# 執行快速啟動腳本
./start.sh
```

#### 方法二：手動啟動

```bash
# 1. 設定環境變數
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"

# 2. 啟動虛擬環境
source .venv/bin/activate

# 3. 啟動 CLI
python cli.py
```

#### CLI 選單功能

```
Design Review Support System
暖感工業風格 | 琥珀橙主題

請選擇功能：
 ❯ [1] 🔍 新增審查
   [2] 📊 查歷史記錄
   [3] 📚 管理知識庫
   [Q] 🚪 退出系統
```

**功能說明**:
- **[1] 🔍 新增審查** - 執行新的設計審查，輸入專案名稱後自動執行四位專家審查，結果寫入資料庫
- **[2] 📊 查歷史記錄** - 顯示最近 10 筆審查記錄，包含風險統計與裁決摘要
- **[3] 📚 管理知識庫** - 檢視知識庫結構（Phase A 為預覽模式）
- **[Q] 🚪 退出系統** - 離開 CLI 介面

#### 視覺風格

CLI 採用**暖感工業風格**設計：
- 🎨 主背景：深炭黑 (#1A1A1B)
- 🟠 重點色：琥珀橙 (#F39C12)
- 🔶 次要色：深橙 (#D35400)
- 📊 Rich Panel + Table 美化
- ✨ Emoji 圖示增強體驗

### 📜 傳統模式（向後相容）

若您需要直接執行核心引擎（例如批次處理或自動化測試）：

```bash
# 使用專案虛擬環境
source .venv/bin/activate
python design_decision_engine.py

# 或直接執行
.venv/bin/python design_decision_engine.py
```

⚠️ **重要提醒**：
- 首次執行請準備好 NVIDIA API 金鑰
- 預留至少 5-10 分鐘的執行時間
- 建議在網路穩定的環境下執行
- 部分模型可能超時，屬正常現象
```

### 6. 新增「專案結構」章節

**插入位置**: 在「使用方式」章節之後、「測試」章節之前

```markdown
## 📁 專案結構

```
NVIDIA/
├── cli.py                          # 互動式 CLI 入口（353 行）
├── design_decision_engine.py       # 核心引擎（保持不變）
├── test_engine.py                  # 單元測試（5 個案例）
├── README.md                       # 使用手冊（本檔案）
├── CLI_USAGE.md                    # CLI 使用指南（216 行）
├── requirements.txt                # 依賴清單
├── start.sh                        # 快速啟動腳本
├── engine/
│   ├── __init__.py
│   └── loader.py                   # 知識庫載入模組（141 行）
├── db/
│   ├── schema.sql                  # 資料庫結構（30 行）
│   ├── init_db.py                  # 初始化腳本（67 行）
│   └── history.db                  # SQLite 資料庫（24KB）
└── knowledge/
    ├── roles/                      # 專家角色設定
    │   ├── risk_analyst.json       # Risk-Analyst 配置
    │   ├── completeness_reviewer.json  # Completeness-Reviewer 配置
    │   ├── improvement_advisor.json    # Improvement-Advisor 配置
    │   └── aggregator.json         # Aggregator 配置
    ├── standards/                  # 公司規範模板（預留）
    │   └── .gitkeep
    └── risk_templates/             # 風險模板（預留）
        └── .gitkeep
```

### 📂 核心檔案說明

| 檔案 | 行數 | 說明 |
|------|------|------|
| `cli.py` | 353 | 互動式 CLI 入口，Rich + Questionary 實現 |
| `engine/loader.py` | 141 | 知識庫載入模組，含 fallback 機制 |
| `db/schema.sql` | 30 | SQLite DDL，定義 reviews 表格與索引 |
| `db/init_db.py` | 67 | 資料庫初始化腳本，冪等設計 |
| `knowledge/roles/*.json` | ×4 | 專家角色外部化設定 |

### 🗂️ 目錄用途

| 目錄 | 用途 | Phase A 狀態 |
|------|------|-------------|
| `engine/` | 工具函數與載入模組 | ✅ 已實現 |
| `db/` | 資料庫相關檔案 | ✅ 已實現 |
| `knowledge/` | 知識庫（角色 + 規範 + 模板） | ✅ 基礎結構 |
| `openspec/changes/` | OpenSpec 變更管理 | ✅ 使用中 |
```

### 7. 版本紀錄 (L486-)

**在現有的 v1.0.1 之前新增**:

```markdown
## 📝 版本紀錄

### v1.1.0 (2026-04-03) - DSS Phase A 完整版

**✨ 重大更新**: 從 DDE 升級為完整的 DSS

**🎯 新增功能**:
- ✨ **互動式 CLI**：使用 rich + questionary 建構友善介面
- 🎯 **選單功能**：[1] 新增審查、[2] 查歷史記錄、[3] 管理知識庫、[Q] 退出
- 📚 **知識庫系統**：將 ROLES 抽離為 `knowledge/roles/*.json`
- 💾 **SQLite 資料庫**：建立 `db/history.db` 儲存審查歷史
- 🔧 **載入模組**：新增 `engine/loader.py` 支援 fallback 機制
- 🎨 **暖感工業風格**：深炭黑 (#1A1A1B) + 琥珀橙 (#F39C12)
- 📄 **快速啟動腳本**：新增 `start.sh`
- 📖 **CLI 使用指南**：新增 `CLI_USAGE.md`
- 📦 **依賴管理**：新增 `requirements.txt`

**✅ 品質保證**:
- ✅ **測試不退步**：原有 5 個測試案例全部通過
- ✅ **零破壞原則**：`design_decision_engine.py` 完全未修改
- ✅ **完整文件**：README + CLI_USAGE.md 雙重保障

**📊 技術指標**:
- Python: 3.13.5
- 新增程式碼：~900 行（cli.py 353 + loader.py 141 + 其他）
- 資料庫大小：~24KB（初始）
- CLI 啟動時間：< 1 秒
- 歷史查詢時間：< 0.5 秒

### v1.0.1 (2026-04-03) - 修正版
```

## 🎨 格式規範

### Markdown 樣式
- **標題層級**: 維持既有格式（# → ## → ###）
- **程式碼區塊**: 使用 ```bash、```python、```sql 等語法高亮
- **表格**: 使用標準 Markdown 表格語法
- **列表**: 優先使用 `-` 符號，嵌套使用 `  `（兩格縮排）

### Emoji 使用原則
- 📋 概述類
- 🎯 目標/功能類
- ✨ 亮點/新增類
- 💾 資料庫類
- 🖥️ CLI/介面類
- 📚 知識庫/文件類
- 🔧 設定/工具類
- ✅ 測試/驗證類
- ⚠️ 警告/注意類
- 🎨 視覺/設計類

### 色彩代碼
在提及暖感工業風格時，統一使用：
- 深炭黑：`#1A1A1B`
- 琥珀橙：`#F39C12`
- 深橙：`#D35400`

## ✅ 驗收清單

### 內容正確性
- [ ] 標題改為「設計決策支援系統」
- [ ] Phase A 三大亮點已說明
- [ ] DSS 系統架構圖已新增
- [ ] 技術棧表格包含 rich + questionary
- [ ] 安裝指令改為 `pip install -r requirements.txt`
- [ ] 資料庫初始化步驟已新增
- [ ] CLI 啟動方式已說明（兩種方法）
- [ ] CLI 四個選單功能已描述
- [ ] 完整專案結構目錄樹已新增
- [ ] v1.1.0 版本紀錄已新增

### 格式一致性
- [ ] 繁體中文撰寫
- [ ] Emoji 使用一致
- [ ] 表格格式正確
- [ ] 程式碼區塊語法高亮正確
- [ ] 標題層級正確

### 無過時內容
- [ ] 無 `pip install openai pytest` 指令
- [ ] 無僅適用於 DDE 的描述
- [ ] 所有檔案路徑與實際一致

---

**設計狀態**: 完成  
**日期**: 2026-04-03  
**版本**: 1.0
