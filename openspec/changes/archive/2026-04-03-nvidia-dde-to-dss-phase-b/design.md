## Context

**Background:**
- Phase A 已建立 DSS 核心架構，包含 CLI 選單、專家角色分工、Aggregator 裁決機制
- `cli.py` 的選單 [3] `manage_knowledge_base()` 目前僅為佔位符（TODO）
- `knowledge/roles/*.json` 已抽離角色設定，但無法透過 CLI 編輯
- `design_decision_engine.py` 的 timeout=120.0 對 DeepSeek 等模型不足，且無重試機制
- Phase B 目標：將知識庫管理從佔位符轉化為真實功能，並提升引擎穩定性

**Constraints:**
- 不破壞 Phase A 交付物（零破壞原則）
- 知識庫操作以 JSON 檔案為主，不引入新資料庫
- 測試覆蓋率不退步（維持 5/5 passed）
- 保持暖感工業風格 UI 一致性（琥珀橙 #F39C12、深炭黑 #1A1A1B）

**Stakeholders:**
- 工程部門：需共用與維護知識資產
- 系統架構師：需確保系統穩定性與可維護性

## Goals / Non-Goals

**Goals:**
- 完整實現 `cli.py` 選單 [3] 的子選單功能（檢視/編輯角色、匯入規範、管理風險模板）
- 在 `engine/loader.py` 新增知識庫讀寫工具函數
- 將 `design_decision_engine.py` 的 timeout 調整為 300.0，並新增重試機制（最多 2 次，間隔 5 秒）
- 建立 `test_loader.py`，涵蓋所有新增函數的測試
- 確保 pytest 測試全綠（test_engine.py + test_loader.py）

**Non-Goals:**
- 不做多人協作/共享資料庫（Phase C）
- 不做 Web UI（Phase C）
- 不修改 Aggregator 邏輯或專家角色分工
- 不變更既有 API 介面或資料庫結構

## Decisions

### Decision 1: 知識庫管理採用子選單模式

**選擇:** 在 `manage_knowledge_base()` 中實現 5 個子選項的互動式選單

**Alternatives Considered:**
1. **獨立 CLI 命令**（如 `dss manage-roles`）：需修改 main() 邏輯，破壞 Phase A 選單結構
2. **直接編輯 JSON 檔**：不符合「不手動編輯」原則，體驗差

**Rationale:** 
- 子選單模式與 Phase A 的選單 [1][2] 保持一致性
- 符合 questionary 互動式風格，降低學習成本
- 零破壞既有程式碼結構

### Decision 2: 知識庫儲存格式維持 JSON

**選擇:** 繼續使用 JSON 作為知識庫儲存格式，不引入 SQLite 或其他資料庫

**Alternatives Considered:**
1. **SQLite**: 支援查詢與事務，但需引入新依賴（sqlite3 已內建但需 schema 設計）
2. **YAML**: 易讀性高，但需額外 dependency（PyYAML）

**Rationale:**
- Phase A 已使用 JSON 儲存角色設定，保持一致性
- Python 內建 json 模組，無需額外依賴
- 符合「知識庫操作以 JSON 檔案為主」的原則

### Decision 3: 重試機制採用指數退避簡化版

**選擇:** 固定間隔 5 秒，最多重試 2 次（非指數遞增）

**Alternatives Considered:**
1. **指數退避**（1s, 2s, 4s）：較複雜，需計算等待時間
2. **無間隔立即重試**: 可能觸發 API rate limit

**Rationale:**
- 簡單易實現，符合「提升穩定性但不過度設計」原則
- 5 秒間隔足夠讓 NVIDIA API 恢復，避免 rate limit
- 2 次重試在穩定性與耗時之間取得平衡（總等待 ≤ 10 秒）

### Decision 4: Timeout 調整為 300.0 秒

**選擇:** 從 120.0 調整為 300.0 秒（5 分鐘）

**Rationale:**
- DeepSeek-V3.2 處理複雜規格時可能需 2-3 分鐘
- 120 秒已知不足（Phase A 實測偶發超時）
- 300 秒提供足夠緩衝，避免過早放棄
- 搭配重試機制，總等待時間可控（≤ 5 分鐘 + 10 秒重試）

### Decision 5: 測試策略

**選擇:** 為 loader.py 新增函數建立獨立測試檔 `test_loader.py`

**Rationale:**
- 與 `test_engine.py` 分離，職責清晰
- 易於單獨執行知識庫相關測試
- 符合 Python 測試慣例（一模組一測試檔）

## Risks / Trade-offs

**[Risk] 編輯角色 Prompt 時可能誤刪重要內容**
→ **Mitigation:** 
  - 編輯前自動備份原檔案（.bak 副檔名）
  - 提供確認步驟後才寫入

**[Risk] 匯入公司規範時可能匯入惡意檔案**
→ **Mitigation:**
  - 限制副檔名僅 .md/.txt
  - 檢查檔案大小上限（1MB）
  - 路徑遍歷防護（只允許寫入 knowledge/standards/）

**[Risk] 重試機制增加總執行時間**
→ **Trade-off:** 
  - 最壞情況：3 位專家 × 2 次重試 × 5 秒 = 額外 30 秒
  - 換取成功率提升，可接受

**[Risk] Timeout 延長可能導致使用者等待過久**
→ **Mitigation:**
  - CLI 顯示進度提示（「正在執行多專家審查...」）
  - 未來可考慮非同步機制（Phase C）

## Migration Plan

**部署步驟:**
1. 備份現有 `cli.py`, `design_decision_engine.py`, `engine/loader.py`
2. 應用 Phase B 修改
3. 執行 `pytest test_engine.py test_loader.py -v` 驗證測試通過
4. 執行 `python cli.py` 手動測試選單 [3] 功能

**Rollback Strategy:**
- Git revert Phase B commit
- 還原備份檔案
- 重新執行測試確認回滾成功

## Open Questions

無（Phase B 範圍明確，技術決策清晰）
