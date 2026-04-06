# nvidia-dde-readme-update - 提案概述

## 📋 變更目標

更新 `README.md` 以完整反映 **Phase A (DDE → DSS)** 的所有改動，確保文件與現有程式碼完全一致。

## 🎯 更新範圍

### 1. 專案標題與概述
**現狀**: 標題為「設計決策引擎 (Design Decision Engine)」  
**更新**: 改為「設計決策支援系統 (Design Decision Support System)」

**新增內容**:
- 說明從 DDE 升級為 DSS 的背景
- 強調 Phase A 新增的三大功能：
  - 互動式 CLI 介面
  - 知識庫系統
  - SQLite 歷史記錄

### 2. 技術棧表格
**新增依賴**:
| 項目 | 版本 | 用途 |
|------|------|------|
| **rich** | >=13.0 | CLI 介面美化 |
| **questionary** | >=2.0 | 互動式選單 |

### 3. 系統架構圖
**新增 DSS 層次結構**:

```
┌─────────────────────────────────────────────────────────┐
│                    cli.py (互動式入口)                   │
│   [1] 新增審查  [2] 查歷史  [3] 知識庫  [Q] 退出         │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  engine/      │  │  knowledge/   │  │  db/          │
│  loader.py    │  │  roles/       │  │  history.db   │
│  (載入模組)   │  │  standards/   │  │  (SQLite)     │
└───────┬───────┘  │  risk_templates│ └───────────────┘
        │          └───────────────┘
        ▼
┌─────────────────────────────────────────────────────────┐
│        design_decision_engine.py (核心引擎)              │
│   Risk-Analyst + Completeness-Reviewer +                │
│   Improvement-Advisor + Aggregator                      │
└─────────────────────────────────────────────────────────┘
```

### 4. 安裝與設定
**更新前**:
```bash
pip install openai pytest
```

**更新後**:
```bash
# 安裝所有依賴
source .venv/bin/activate
pip install -r requirements.txt

# 初始化資料庫（首次執行）
python db/init_db.py
```

### 5. 使用方式
**新增 CLI 啟動章節**:

#### 方法一：快速啟動（推薦）
```bash
export NVIDIA_API_KEY="nvapi-YOUR_KEY"
./start.sh
```

#### 方法二：互動式 CLI
```bash
source .venv/bin/activate
python cli.py
```

**CLI 選單功能說明**:
- `[1] 🔍 新增審查` - 執行新的設計審查
- `[2] 📊 查歷史記錄` - 查看最近 10 筆記錄
- `[3] 📚 管理知識庫` - 知識庫管理（Phase A 預覽）
- `[Q] 🚪 退出系統` - 離開系統

**保留傳統模式**:
```bash
python design_decision_engine.py
```

### 6. 專案結構
**新增完整目錄樹**:

```
NVIDIA/
├── cli.py                          # 互動式 CLI 入口（353 行）
├── design_decision_engine.py       # 核心引擎（保持不變）
├── test_engine.py                  # 單元測試
├── README.md                       # 使用手冊
├── CLI_USAGE.md                    # CLI 使用指南
├── requirements.txt                # 依賴清單
├── start.sh                        # 快速啟動腳本
├── engine/
│   ├── __init__.py
│   └── loader.py                   # 知識庫載入模組（141 行）
├── db/
│   ├── schema.sql                  # 資料庫結構
│   ├── init_db.py                  # 初始化腳本
│   └── history.db                  # SQLite 資料庫（24KB）
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

### 7. 版本紀錄
**新增 v1.1.0 (2026-04-03)**:

```
### v1.1.0 (2026-04-03) - DSS Phase A 完整版
✨ 新增互動式 CLI：使用 rich + questionary 建構友善介面
🎯 選單功能：[1] 新增審查、[2] 查歷史記錄、[3] 管理知識庫、[Q] 退出
📚 知識庫系統：將 ROLES 抽離為 knowledge/roles/*.json
💾 SQLite 資料庫：建立 db/history.db 儲存審查歷史
🔧 載入模組：新增 engine/loader.py 支援 fallback 機制
🎨 暖感工業風格：深炭黑 (#1A1A1B) + 琥珀橙 (#F39C12)
📄 快速啟動腳本：新增 start.sh
📖 CLI 使用指南：新增 CLI_USAGE.md
✅ 測試不退步：原有 5 個測試案例全部通過
📦 依賴管理：新增 requirements.txt
```

## ✅ 驗收條件

### 文件一致性
- [ ] README.md 版本號更新為 v1.1.0
- [ ] 專案結構目錄樹與實際檔案一致
- [ ] 所有 Phase A 新增檔案都出現在目錄樹中

### 內容正確性
- [ ] 無任何過時的安裝指令（不再出現 `pip install openai pytest`）
- [ ] 架構圖包含 CLI + DB + Knowledge Base 層
- [ ] 技術棧表格包含 rich 和 questionary

### 格式完整性
- [ ] 保留原有文件風格（繁體中文、emoji、表格格式）
- [ ] 只更新過時內容，不刪除仍然有效的章節
- [ ] 版本紀錄格式與其他章節一致

## 🎨 設計原則

### 文件風格
- ✅ 使用繁體中文（zh_TW）
- ✅ 適當使用 emoji 增強可讀性
- ✅ 保持表格、程式碼區塊格式一致
- ✅ 溫暖專業的語氣（解憂系特質）

### 視覺風格
- 🎨 主背景：深炭黑 (#1A1A1B)
- 🟠 重點色：琥珀橙 (#F39C12)
- 🔶 次要色：深橙 (#D35400)
- 📊 高對比、警覺性強但溫暖不刺眼

## 📝 更新策略

### 最小改動原則
1. **標题更新**: 只修改專案名稱與概述
2. **章節新增**: 在既有章節後追加新內容
3. **替換過時資訊**: 安裝指令、使用方式
4. **保留有效內容**: 核心概念、AI 模型介紹、錯誤處理等

### 結構優化
- 在「系統架構」章節新增 DSS 層次圖
- 在「技術棧」章節新增 CLI 相關依賴
- 在「使用方式」章節優先推薦 CLI
- 在「專案結構」章節展示完整目錄樹

## 🚀 預期效益

### 對使用者
- 📖 清晰的升級路徑說明
- 🚀 快速找到 CLI 啟動方式
- 💡 理解 DSS 與 DDE 的差異
- 🎯 準確的檔案位置參考

### 對維護者
- 📋 完整的版本变更记录
- 🔍 容易追蹤改動脈絡
- ✅ 文件與程式碼同步
- 🏗️ 清晰的系統架構視圖

---

**提案狀態**: 待審核  
**建立日期**: 2026-04-03  
**負責人**: AI Assistant  
**版本**: 1.0
