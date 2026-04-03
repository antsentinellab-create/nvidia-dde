## Why

Phase A 已完成 DSS 核心架構與 CLI 選單 [3] 的佔位符，但知識庫管理功能尚未實現，工程部門無法共用與維護知識資產。同時，引擎穩定性不足（timeout 僅 120 秒、無重試機制），導致 DeepSeek 等模型易超時失敗。本 Phase B 旨在將這些佔位符轉化為真實功能，讓 DSS 真正可用於生產環境。

## What Changes

- **CLI 選單 [3] 從佔位符變成完整功能**：實現 `manage_knowledge_base()` 子選單，支援檢視/編輯角色設定、匯入公司規範、管理風險模板
- **知識庫工具函數擴充**：在 `engine/loader.py` 新增 `save_role()`, `load_standards()`, `load_risk_templates()`, `save_risk_template()` 函數
- **引擎穩定性強化**：在 `design_decision_engine.py` 將 timeout 從 120.0 調整為 300.0，並新增重試機制（每個專家最多重試 2 次，間隔 5 秒）
- **新增測試覆蓋**：建立 `test_loader.py`，涵蓋 loader.py 的新增函數，確保測試覆蓋率不退步（維持 5/5 passed）

## Capabilities

### New Capabilities
- `knowledge-base-management`: CLI 知識庫管理功能，包含角色檢視/編輯、規範匯入、風險模板管理
- `engine-retry-mechanism`: API 呼叫重試機制與 timeout 調整，提升系統穩定性
- `loader-utilities`: loader.py 的新增工具函數，支援知識庫讀寫操作

### Modified Capabilities
- 無（Phase B 不修改既有 spec 層級行為，僅實現原有功能的佔位符）

## Impact

- **修改檔案**:
  - `cli.py`: 實現 `manage_knowledge_base()` 子選單邏輯
  - `design_decision_engine.py`: 調整 `get_client()` timeout 參數，新增重試迴圈
  - `engine/loader.py`: 新增 4 個工具函數
  - `test_loader.py`: 新增測試檔案
  
- **依賴關係**:
  - 知識庫操作以 JSON 檔案為主，不引入新資料庫
  - 保持與 Phase A 相容，零破壞既有功能
  
- **API 變更**:
  - 無外部 API 變更，僅內部穩定性強化
  
- **系統影響**:
  - 提升 LLM API 呼叫成功率（尤其是 DeepSeek 等耗時模型）
  - 工程部門可透過 CLI 直接管理知識資產，無需手動編輯 JSON
