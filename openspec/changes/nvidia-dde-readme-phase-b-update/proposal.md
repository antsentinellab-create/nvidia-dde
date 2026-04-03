## Why

Phase B 已完成知識庫管理功能與引擎穩定性強化，但 README.md 仍停留在 v1.1.0（Phase A）。為確保文件與程式碼同步，需更新 README 反映所有 Phase B 改動，包括 CLI 選單 [3] 完整功能、重試機制、timeout 調整，以及新增的測試檔案。

## What Changes

- **版本號更新**: v1.1.0 → v1.2.0（Phase B 完整版）
- **新增功能說明**: 
  - CLI 選單 [3] 知識庫管理子選單詳細說明（[3-1] 到 [3-5]）
  - 引擎穩定性：timeout 300 秒、重試機制 2 次
- **系統架構圖更新**: 標註 knowledge/standards/ 與 knowledge/risk_templates/ 已實現
- **專案結構更新**: 
  - 新增 `test_loader.py`（10 個測試案例）
  - 標註 `engine/loader.py` 新增 4 個工具函數
- **版本紀錄新增**: v1.2.0 章節，列出 Phase B 所有改動

## Capabilities

### New Capabilities
- `readme-documentation`: README.md 文件更新，涵蓋 Phase B 所有功能改動

### Modified Capabilities
- 無（僅更新文件，不修改既有 spec 層級行為）

## Impact

- **修改檔案**:
  - `README.md`: 更新版本號、功能說明、架構圖、專案結構、版本紀錄
  
- **依賴關係**:
  - 無新依賴，僅文件更新
  
- **API 變更**:
  - 無外部 API 變更
  
- **系統影響**:
  - 提升文件準確性與完整性
  - 幫助使用者理解 Phase B 新增功能（知識庫管理、重試機制）
  - 維持 MIT License 相容性
