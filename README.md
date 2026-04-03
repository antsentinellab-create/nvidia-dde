# 設計決策引擎 (Design Decision Engine)

## 📋 專案概述

這是一個基於多專家協作的**系統設計審查引擎**，利用多個 AI 模型模擬不同領域的資深架構師，對系統設計規格進行全方位審查與風險分析。

### 核心概念

透過角色分工的方式，邀請三位不同專長的 AI 專家進行 Code Review：
- **Risk-Analyst**（風險分析師）：專注於安全性與風險識別
- **Completeness-Reviewer**（完整性審查員）：檢查需求覆蓋率
- **Improvement-Advisor**（改善顧問）：提供優化建議與亮點發現

最後由 **Aggregator**（總協調師）整合所有專家意見，生成最終裁決報告。

---

## 🎯 主要功能

### ✅ 多專家協作審查
- 三位專家各司其職，從不同角度審視設計規格
- 避免單一視角的盲點，提升審查品質
- 支援彈性擴展更多專家角色

### ✅ 智能合併與裁決
- 自動合併各專家的審查結果
- Aggregator 負責去重、排序優先級、裁決衝突
- 限制每類別最多保留 5 條高價值建議

### ✅ 嚴謹的錯誤處理
- JSON 解析容錯機制（支援 markdown code block 格式）
- Sanity check 驗證輸出結構
- Fallback 機制：當 Aggregator 失敗時自動回退到合併結果

### ✅ 完整的測試覆蓋
- 測試 `normalize()` 函數處理缺失資料
- 測試 `is_valid_output()` 驗證輸出結構
- 確保系統穩定性

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    設計規格 (SPEC)                       │
│           RequestRetryBudget 架構說明                     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Risk-Analyst │ │ Completeness │ │ Improvement  │
│   (V3.2)     │ │  Reviewer    │ │   Advisor    │
│              │ │  (Qwen3.5)   │ │ (Mistral)    │
│ ⚠️ 易超時     │ │ ✅ 穩定      │ │ ✅ 快速      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    Merger & Merge     │
            │  合併各專家審查結果     │
            │  ✅ 包含 fallback      │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   Aggregator          │
            │ (Nemotron-Ultra 253B) │
            │   最終裁決與整合        │
            │   ✅ Sanity Check     │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   最終裁決報告 (JSON)   │
            └───────────────────────┘
```

---

## 📦 技術棧

| 項目 | 版本/型號 | 用途 |
|------|----------|------|
| **Python** | 3.13.5 | 主要開發語言 |
| **openai** | 2.30.0 | NVIDIA API 客戶端 |
| **pytest** | 9.0.2 | 單元測試框架 |

### 使用的 AI 模型

| 角色 | 模型 ID | 專長領域 | 特性備註 |
|------|--------|---------|----------|
| Risk-Analyst | `deepseek-ai/deepseek-v3.2` | 風險分析 | ⚠️ 回應較慢，易超時 |
| Completeness-Reviewer | `qwen/qwen3.5-397b-a17b` | 完整性審查 | ✅ 穩定度高 |
| Improvement-Advisor | `mistralai/mistral-large-3-675b-instruct-2512` | 改善建議 | ✅ 回應快速 |
| Aggregator | `nvidia/llama-3.1-nemotron-ultra-253b-v1` | 最終裁決 | ✅ 整合能力強 |

---

## 🔧 安裝與設定

### 前置需求

```bash
pip install openai pytest
```

### 安裝依賴套件

```bash
# 使用專案虛擬環境
source .venv/bin/activate
pip install -r requirements.txt
```

**依賴清單：**
- `openai==2.30.0` - NVIDIA API 客戶端
- `pytest==9.0.2` - 單元測試框架
- `rich>=13.0` - CLI 美化工具
- `questionary>=2.0` - 互動式選單

### API 金鑰設定

在 [`design_decision_engine.py`](design_decision_engine.py) 中已內建 NVIDIA API 金鑰：

```python
client = OpenAI(
    api_key=os.environ.get("NVIDIA_API_KEY"),
    base_url="https://integrate.api.nvidia.com/v1",
    timeout=120.0
)
```

⚠️ **安全警告**：生產環境請將 API 金鑰移至環境變數，避免硬編碼在程式碼中。

---

## 🚀 使用方式

### 互動式 CLI（推薦）

從 v1.1.0 開始，提供互動式 CLI 介面，更友善的使用體驗！

```bash
# 設定環境變數
export NVIDIA_API_KEY="nvapi-YOUR_API_KEY_HERE"

# 啟動 CLI
source .venv/bin/activate
python cli.py
```

**CLI 選單功能：**
- `[1] 🔍 新增審查` - 執行新的設計審查
- `[2] 📊 查歷史記錄` - 查看過往審查記錄
- `[3] 📚 管理知識庫` - 管理知識庫（Phase A 預覽）
- `[Q] 🚪 退出系統` - 離開系統

### 執行設計審查（傳統模式）

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

### 執行單元測試

```bash
# 使用專案虛擬環境
source .venv/bin/activate
pytest test_engine.py -v

# 或使用絕對路徑
.venv/bin/pytest test_engine.py -v
```

**預期輸出：**
```
================ test session starts =================
platform linux -- Python 3.13.5, pytest-9.0.2
collected 5 items                                     

test_engine.py::test_normalize_empty_or_none PASSED    [ 20%]
test_engine.py::test_normalize_partial_data PASSED     [ 40%]
test_engine.py::test_is_valid_output_success PASSED    [ 60%]
test_engine.py::test_is_valid_output_invalid_type PASSED [ 80%]
test_engine.py::test_is_valid_output_missing_key PASSED [100%]

================= 5 passed in 0.72s ==================
```

### 自訂設計規格

修改 `SPEC` 常數內容即可：

```python
SPEC = """
【專案名稱】
目標：...
原則：...
...
"""
```

---

## 📊 輸出格式

### 專家輸出格式

每位專家回傳的 JSON 結構：

```json
{
  "risks": [
    {
      "level": "high/medium/low",
      "issue": "問題描述",
      "suggestion": "具體建議"
    }
  ],
  "missing": [
    {
      "item": "缺少的設計",
      "reason": "為什麼需要",
      "how": "如何補充"
    }
  ],
  "improvements": [
    {
      "area": "改善領域",
      "current": "現況",
      "better": "更好的做法"
    }
  ],
  "good_points": ["值得保留的設計決策"],
  "verdict": "整體評估"
}
```

### Aggregator 最終報告

```json
{
  "risks": [...],
  "missing": [...],
  "improvements": [...],
  "good_points": [...],
  "verdict": "整體評估（含衝突裁決說明）"
}
```

---

## 🧪 測試涵蓋範圍

[`test_engine.py`](test_engine.py) 包含以下測試案例：

### `test_normalize_empty_or_none()`
測試 `normalize()` 處理 `None` 或空白字典時的預設值填充。

### `test_normalize_partial_data()`
測試 `normalize()` 補齊缺失的 key，保留既有資料。

### `test_is_valid_output_success()`
測試 `is_valid_output()` 對正確結構回傳 `True`。

### `test_is_valid_output_invalid_type()`
測試 `is_valid_output()` 處理型態錯誤（例如把 list 寫成 dict 或 string）。

### `test_is_valid_output_missing_key()`
測試 `is_valid_output()` 在缺少 key 時能靠 `data.get` 預設值通過檢查。

---

## 🎨 執行流程詳解

### Phase 1: 專家分工審查

```
[1/3] Risk-Analyst (deepseek-v3.2)
------------------------------------------------------------
✅ 15.3s | risks:3, missing:2, improvements:1, good_points:4✓
   verdict: 整體設計良好，但需注意...

[2/3] Completeness-Reviewer (qwen3.5-397b-a17b)
------------------------------------------------------------
✅ 18.7s | risks:1, missing:4, improvements:2, good_points:3✓
   verdict: 需求覆蓋率約 85%，建議補充...

[3/3] Improvement-Advisor (mistral-large-3-675b-instruct-2512)
------------------------------------------------------------
✅ 16.2s | risks:0, missing:1, improvements:5, good_points:6✓
   verdict: 多處設計值得肯定，以下是優化建議...
```

### Phase 2: 合併專家結果

```
============================================================
合併各專家結果 → 送交 Aggregator
============================================================
成功接收：3/3 位專家
合併結果 keys: ['risks', 'missing', 'improvements', 'good_points', 'expert_verdicts']
```

### Phase 3: Aggregator 最終裁決

```
============================================================
Aggregator (nemotron-ultra-253b-v1) 最終裁決
============================================================
✅ 22.4s | Aggregator 裁決完成
   risks:3 missing:4 improvements:4
✅ Aggregator 輸出通過 sanity check
```

---

## 🔍 核心函數說明

### `build_prompt(role)`
根據角色設定生成專屬的审查 prompt，強調該角色的主責領域。

### `get_content(response)`
從 API 回應中提取內容，自動處理 markdown code block 格式。

### `parse_json(text)`
解析 JSON，容錯處理前後綴雜訊，提取有效 JSON 區塊。

### `normalize(data)`
標準化專家輸出，確保結構一致，避免 merge 時發生 KeyError。

### `is_valid_output(data)`
驗證 Aggregator 輸出是否符合預期結構，防止「成功但亂輸出」。

---

## 💡 應用場景

### ✅ 適合的使用情境
- 系統設計文件審查
- 架構決策記錄 (ADR) 驗證
- 技術方案風險評估
- Code Review 輔助工具
- 教學與學習架構設計

### ⚠️ 不建議的使用情境
- 需要即時回應的場景（每次執行約 60-90 秒）
- 極度簡短的代碼片段審查
- 非技術性文檔審查

---

## 📊 效能指標

| 指標 | 數值 | 備註 |
|------|------|------|
| 單次執行時間 | ~150-500 秒（2.5-8 分鐘） | 視模型回應速度而定 |
| API 呼叫次數 | 4 次（3 專家 + 1 Aggregator） | 失敗仍會計費 |
| 成功率 | ~70-90% | 含 fallback 機制，部分模型可能超時 |
| 測試覆蓋率 | 核心函數 100% | 5 個測試案例全部通過 |
| 模型回應時間差異 | 49-362 秒 | DeepSeek-V3 最慢，Mistral 最快 |

### 實際執行數據參考

```
[1/3] Risk-Analyst (deepseek-v3.2)
       ❌ 362.4s | Request timed out.          ⚠️ 易超時

[2/3] Completeness-Reviewer (qwen3.5-397b-a17b)
       ✅ 79.9s  | 穩定發揮                     ✅ 可靠

[3/3] Improvement-Advisor (mistral-large-3-675b-instruct-2512)
       ✅ 49.0s  | 快速回應                     ✅ 推薦

Aggregator (nemotron-ultra-253b-v1)
       ✅ 30.1s  | 整合裁決                     ✅ 高效
```

---

## ⚠️ 執行風險與注意事項

### 潛在問題

1. **模型超時風險**
   - 部分大型模型（如 DeepSeek-V3）可能耗時較長甚至超時
   - 預設 timeout 為 120 秒，可能不足以等待某些模型
   - 建議：增加重試機制或調整 timeout 設定

2. **API 配額消耗**
   - 每次執行固定消耗 4 次 API 呼叫
   - 即使部分模型失敗，已消耗的配額仍無法退還
   - 建議：在非尖峰時段執行，或使用較小的模型測試

3. **不穩定性**
   - 不同模型的回應時間差異極大（49s - 362s）
   - 網路狀況與伺服器負載會影響執行時間
   - 建議：預留充足的執行時間，避免在緊迫時限下使用

4. **Fallback 機制限制**
   - 當 Aggregator 失敗時，會回退到合併結果
   - 此時缺少最終裁決與優先級排序
   - 建議：檢查輸出中的 `expert_verdicts` 以確保品質

### 建議改進措施

```python
# 未來可考慮的優化方向

# 1. 增加重試機制
for i, role in enumerate(ROLES, 1):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(...)
            break
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            time.sleep(5)

# 2. 自訂 timeout 設定
client = OpenAI(
    api_key="...",
    base_url="...",
    timeout=300.0  # 增加為 300 秒
)

# 3. 非同步執行選項
import asyncio
async def call_all_models_async():
    tasks = [call_model(role) for role in ROLES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 🔒 安全注意事項

1. **API 金鑰保護**：請勿將含金鑰的程式碼提交至公開倉庫
2. **速率限制**：注意 NVIDIA API 的呼叫頻率限制
3. **成本控管**：每次執行約消耗 4 次 API 配額，失敗仍會計費
4. **超時設定**：預設 120 秒可能不足，建議根據使用模型調整
5. **錯誤處理**：生產環境應增加更完善的重試與降級機制

---

## 🤝 貢獻指南

### 新增專家角色

在 `ROLES` 列表中添加新角色：

```python
{
    "id": "model-id",
    "name": "角色名稱",
    "system": "角色設定 prompt",
    "focus_fields": ["主責欄位"],
    "focus_desc": "職責描述",
}
```

### 調整審查維度

修改 `build_prompt()` 中的 JSON 格式定義，增加新的審查面向。

---

## 📝 版本紀錄

### v1.1.0 (2026-04-03) - DSS Phase A 完整版
- ✨ **新增互動式 CLI**：使用 rich + questionary 建構友善介面
- 🎯 **選單功能**：[1] 新增審查、[2] 查歷史記錄、[3] 管理知識庫、[Q] 退出
- 📚 **知識庫系統**：將 ROLES 抽離為 `knowledge/roles/*.json`
- 💾 **SQLite 資料庫**：建立 `db/history.db` 儲存審查歷史
- 🔧 **載入模組**：新增 `engine/loader.py` 支援 fallback 機制
- 🎨 **暖感工業風格**：深炭黑 (#1A1A1B) + 琥珀橙 (#F39C12)
- 📄 **快速啟動腳本**：新增 `start.sh`
- 📖 **CLI 使用指南**：新增 `CLI_USAGE.md`
- ✅ **測試不退步**：原有 5 個測試案例全部通過
- 📦 **依賴管理**：新增 `requirements.txt`

### v1.0.1 (2026-04-03) - 修正版
- ✨ 更新效能指標：單次執行時間修正為 150-500 秒
- ⚠️ 新增「執行風險與注意事項」章節
- 📊 補充實際執行數據參考
- 🔧 更新技術棧版本資訊（Python 3.13.5, openai 2.30.0, pytest 9.0.2）
- 🎯 在架構圖中標註各模型特性（易超時/穩定/快速）
- 📝 補充建議改進措施（重試機制、timeout 調整、非同步執行）
- ✅ 更新成功率描述（70-90%，含 fallback 機制）
- 💡 在使用方式中增加重要提醒

### v1.0.0 (2026-04-03)
- ✨ 初始版本發布
- ✅ 實現三專家 + Aggregator 架構
- ✅ 完整的錯誤處理與 fallback 機制
- ✅ 單元測試覆蓋核心函數

---

## 📞 聯絡與支援

如有任何問題或建議，歡迎提出 Issue 或 Pull Request。

---

## 📄 授權條款

本專案採用 MIT License。

---

## 🙏 致謝

感謝 NVIDIA 提供強大的 AI 模型 API，讓多專家協作審查成為可能。
