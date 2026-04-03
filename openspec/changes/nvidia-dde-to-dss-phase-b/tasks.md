## 1. 知識庫工具函數實現 (engine/loader.py)

- [x] 1.1 新增 `save_role(filename, data)` 函數：將角色設定寫入 knowledge/roles/*.json
- [x] 1.2 新增 `load_standards()` 函數：讀取 knowledge/standards/ 所有 .md/.txt 檔案
- [x] 1.3 新增 `load_risk_templates()` 函數：讀取 knowledge/risk_templates/ 所有 .json 檔案
- [x] 1.4 新增 `save_risk_template(name, data)` 函數：將風險模板寫入 knowledge/risk_templates/*.json

## 2. CLI 知識庫管理功能實現 (cli.py)

- [x] 2.1 實現 `manage_knowledge_base()` 主函數：建立子選單架構
- [x] 2.2 實現子選單 [3-1]「檢視所有角色設定」：載入並顯示 knowledge/roles/*.json 內容
- [x] 2.3 實現子選單 [3-2]「編輯角色 Prompt」：互動式修改 system 欄位並寫回 JSON
- [x] 2.4 實現子選單 [3-3]「匯入公司設計規範」：選擇 .md/.txt 檔案並複製至 knowledge/standards/
- [x] 2.5 實現子選單 [3-4]「檢視風險模板」：載入並顯示 knowledge/risk_templates/*.json 內容
- [x] 2.6 實現子選單 [3-5]「新增風險模板」：互動式填寫 level/issue/suggestion 並儲存
- [x] 2.7 實現子選單 [B]「返回主選單」：回到上層選單

## 3. 引擎穩定性強化 (design_decision_engine.py)

- [x] 3.1 將 `get_client()` 的 timeout 從 120.0 調整為 300.0
- [x] 3.2 在 `run_design_review()` 中新增專家呼叫重試邏輯（最多 2 次，間隔 5 秒）
- [x] 3.3 重試時印出明確訊息：「重試 1/2...」、「重試 2/2...」
- [x] 3.4 確保重試失敗後才記錄錯誤並繼續下一位專家

## 4. 測試覆蓋 (test_loader.py)

- [x] 4.1 建立 test_loader.py 測試檔
- [x] 4.2 實現 `test_load_roles_success()`: 測試成功載入 roles
- [x] 4.3 實現 `test_load_roles_fallback()`: 測試載入失敗時的 fallback 機制
- [x] 4.4 實現 `test_save_and_load_role()`: 測試 save_role + load_role 迴圈
- [x] 4.5 實現 `test_load_standards_empty()`: 測試 standards 目錄為空的情況
- [x] 4.6 實現 `test_save_risk_template()`: 測試風險模板的儲存與載入

## 5. 驗收與測試執行

- [x] 5.1 執行 `pytest test_engine.py test_loader.py -v`，確認所有測試通過
- [x] 5.2 執行 `python cli.py`，手動測試選單 [3] 進入子選單
- [x] 5.3 測試 [3-2] 修改角色 prompt 並確認寫回 JSON
- [x] 5.4 測試 [3-3] 匯入 .md 檔案至 knowledge/standards/
- [x] 5.5 測試 [3-5] 新增風險模板並確認儲存成功
- [x] 5.6 確認 design_decision_engine.py timeout 已改為 300.0
- [x] 5.7 模擬專家失敗情境，確認印出「重試 1/2...」訊息
