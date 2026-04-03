## Context

**Background:**
- README.md 目前版本為 v1.1.0（Phase A），描述包含 CLI 選單 [1][2] 與知識庫基本架構
- Phase B 已實現：
  - CLI 選單 [3] 完整子選單功能（[3-1] 到 [3-5]）
  - `engine/loader.py` 新增 4 個工具函數（save_role, load_standards, load_risk_templates, save_risk_template）
  - `design_decision_engine.py` timeout 調整為 300 秒 + 重試機制（最多 2 次）
  - `test_loader.py` 新增 10 個測試案例
- 文件與程式碼不同步，可能造成使用者困惑

**Current State:**
- README 章節 7.1 仍標註 v1.1.0
- 專案結構未列出 test_loader.py
- 系統架構圖未標註 knowledge/standards/ 與 risk_templates/ 已實現
- 無 Phase B 相關功能說明

**Constraints:**
- 保持現有 README 結構與風格一致性
- 使用繁體中文
- 維持暖感工業風格視覺元素（emoji、格式）

## Goals / Non-Goals

**Goals:**
- 更新版本號 v1.1.0 → v1.2.0
- 在「主要功能」章節新增 Phase B 功能說明
- 更新系統架構圖，標註知識庫子目錄已實現
- 在專案結構中新增 test_loader.py
- 在版本紀錄中新增 v1.2.0 章節
- 確保所有連結與參照正確

**Non-Goals:**
- 不修改既有功能描述（Phase A 內容保持不變）
- 不變更 README 整體結構
- 不引入新的章節或區塊
- 不修改技術棧表格（Phase B 無新依賴）

## Decisions

### Decision 1: 版本號採語義化版本

**選擇:** v1.2.0（minor version bump）

**Rationale:**
- Phase B 新增功能但未破壞既有 API（零破壞原則）
- 符合語義化版本規範（major.minor.patch）
- 與 Phase A 的 v1.1.0 保持連續性

### Decision 2: 在既有章節中增量更新

**選擇:** 在現有章節中新增內容，而非建立獨立 Phase B 章節

**Rationale:**
- 避免文件碎片化
- 使用者無需跳轉多個章節
- 保持文件單一真實來源（Single Source of Truth）

### Decision 3: 系統架構圖微調

**選擇:** 在既有架構圖中標註已實現的目錄，不重繪整體架構

**Rationale:**
- Phase B 未改變核心架構
- 最小改動原則
- 保持視覺一致性

### Decision 4: 版本紀錄詳細條列

**選擇:** 在 v1.2.0 章節中詳細條列所有 Phase B 改動

**Rationale:**
- 方便使用者快速了解升級內容
- 符合開源專案慣例
- 幫助既有使用者評估是否升級

## Risks / Trade-offs

**[Risk] 文件過長**
→ **Trade-off:** 
  - README 已達 724 行，新增內容可能更長
  - 但保持單一文件完整性，利於維護

**[Risk] 遺漏其他改動**
→ **Mitigation:**
  - 對照 Phase-B tasks.md 逐一檢查
  - 確保所有改動都有反映

**[Risk] 格式不一致**
→ **Mitigation:**
  - 嚴格遵循現有 Markdown 格式
  - 使用相同的 emoji、標題層級、代碼塊風格
