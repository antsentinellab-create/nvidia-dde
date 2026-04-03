# CLI 使用指南

## 🚀 快速開始

### 方法一：使用啟動腳本（推薦）

```bash
# 設定 API 金鑰
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"

# 執行啟動腳本
./start.sh
```

### 方法二：手動啟動

```bash
# 1. 設定環境變數
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"

# 2. 啟動虛擬環境
source .venv/bin/activate

# 3. 啟動 CLI
python cli.py
```

## 📋 CLI 選單功能

### 🔍 [1] 新增審查

執行新的設計審查：

1. 選擇 `[1] 🔍 新增審查`
2. 輸入專案名稱（例如：`RequestRetryBudget`）
3. 確認執行
4. 等待審查完成（約 2-8 分鐘）
5. 查看風險統計摘要
6. 結果自動儲存至資料庫

**審查流程：**
- Risk-Analyst（風險分析）
- Completeness-Reviewer（完整性審查）
- Improvement-Advisor（改善建議）
- Aggregator（最終裁決）

### 📊 [2] 查歷史記錄

查看過往的審查記錄：

1. 選擇 `[2] 📊 查歷史記錄`
2. 系統顯示最近 10 筆記錄
3. 包含欄位：
   - ID：記錄編號
   - 專案名稱
   - 審查時間
   - 高風險數量
   - 中風險數量
   - 低風險數量
   - 裁決摘要

**範例輸出：**
```
┌────┬──────────────┬─────────────────────┬───────┬───────┬───────┬──────────────┐
│ ID │   專案名稱    │     審查時間        │ 高風險 │ 中風險 │ 低風險 │  裁決摘要   │
├────┼──────────────┼─────────────────────┼───────┼───────┼───────┼──────────────┤
│ 1  │ ProjectA     │ 2026-04-03 10:30:00 │   2   │   3   │   1   │ 整體設計良好 │
└────┴──────────────┴─────────────────────┴───────┴───────┴───────┴──────────────┘
```

### 📚 [3] 管理知識庫

管理知識庫設定（Phase A 預覽）：

1. 選擇 `[3] 📚 管理知識庫`
2. 查看知識庫位置
3. 未來將支援：
   - 檢視角色設定
   - 編輯公司規範模板
   - 匯入/匯出風險模板

**目前知識庫位置：**
```
knowledge/
├── roles/
│   ├── risk_analyst.json
│   ├── completeness_reviewer.json
│   ├── improvement_advisor.json
│   └── aggregator.json
├── standards/
│   └── .gitkeep
└── risk_templates/
    └── .gitkeep
```

### 🚪 [Q] 退出系統

離開 CLI 介面。

## ⚙️ 環境設定

### 設定 API 金鑰

**永久設定（推薦）：**

在 `~/.bashrc` 或 `~/.zshrc` 中加入：
```bash
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"
```

然後執行：
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

**臨時設定：**

每次啟動前執行：
```bash
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"
```

### 檢查 API 金鑰

```bash
echo $NVIDIA_API_KEY
```

若顯示空白，表示未設定。

## 🔧 疑難排解

### 問題：找不到 .venv 虛擬環境

**解決方法：**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 問題：模組載入錯誤

**解決方法：**
```bash
# 重新安裝依賴
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 問題：資料庫尚未初始化

**解決方法：**
```bash
python db/init_db.py
```

### 問題：CLI 啟動失敗

**完整重置流程：**
```bash
# 1. 刪除虛擬環境
rm -rf .venv

# 2. 重新建立
python3 -m venv .venv
source .venv/bin/activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 初始化資料庫
python db/init_db.py

# 5. 啟動 CLI
python cli.py
```

## 📊 資料庫查詢

### 查看所有記錄

```bash
sqlite3 db/history.db "SELECT * FROM reviews;"
```

### 查看高風險項目

```bash
sqlite3 db/history.db "SELECT project, risk_high FROM reviews ORDER BY risk_high DESC;"
```

### 清除所有記錄

```bash
sqlite3 db/history.db "DELETE FROM reviews;"
```

## 💡 使用技巧

1. **快速啟動**：使用 `./start.sh` 腳本
2. **API 金鑰管理**：設定環境變數避免每次輸入
3. **定期備份**：備份 `db/history.db` 檔案
4. **知識庫版本控制**：使用 Git 管理 `knowledge/` 目錄

## 📝 快捷鍵

- 使用方向鍵 `↑` `↓` 選擇選單項目
- 按 `Enter` 確認選擇
- 按 `Q` 或選擇 `[Q]` 退出系統

---

**版本**: v1.1.0  
**最後更新**: 2026-04-03
