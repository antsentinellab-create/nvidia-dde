import os
from openai import OpenAI
import time
import json
from typing import Dict
from engine.loader import load_roles as _load_roles

def get_client():
    """延遲初始化 OpenAI client，避免 import 時就需要 API key"""
    return OpenAI(
        api_key=os.environ.get("NVIDIA_API_KEY"),
        base_url="https://integrate.api.nvidia.com/v1",
        timeout=300.0  # Phase B: 從 120.0 調整為 300.0 秒
    )

SPEC = """
【專案規格：RequestRetryBudget】

目標：建立 RequestRetryBudget 解決多層 retry 未爆彈
原則：不修改現有 retry 邏輯，只加全局上限保護

一、新增模組：workflow/retry_budget.py
  class RequestRetryBudget:
      def __init__(self, max_total: int = 10, request_id: str = None)
      def can_retry(self) -> bool
      def consume(self, n: int = 1) -> None
      def remaining(self) -> int
      def is_exhausted(self) -> bool
      def snapshot(self) -> dict
  class RetryBudgetExhaustedError(Exception): pass

  設計原則：
    - Budget 跟著單一 request 傳遞（不是全局單例）
    - 每次 retry 呼叫 consume(1)
    - 耗盡時拋 RetryBudgetExhaustedError
    - 支援 logging snapshot（request_id, consumed, remaining）

二、整合點
  2.1 LLMGateway（gateway/llm_gateway.py）
    - invoke_provider 接受可選的 budget: RequestRetryBudget
    - 每次 retry 前檢查 budget.can_retry()
  2.2 Workflow Engine（workflow/workflow_engine.py）
    - Planning loop 接受 budget
  2.3 Execution Stage（workflow/stages/execution_stage.py）
    - MAX_RETRY loop 接受 budget
  2.4 Route Task（router/task_router.py）
    - 建立 RequestRetryBudget（請求入口點）
    - 傳遞給所有下游呼叫

三、最壞情況保護
  預設 max_total = 10
  LLM Gateway 最多 3 次
  Execution   最多 5 次
  Planning    最多 3 次（保留餘量）
  合計上限    10 次

四、錯誤處理
  RetryBudgetExhaustedError：
    - 記錄 warning log（含 request_id + consumed 次數）
    - 向上傳遞，最終在 TaskRouter 捕獲

五、測試規格
  - 初始 remaining == max_total
  - consume(1) 後 remaining == max_total - 1
  - 耗盡時 can_retry() == False
  - 耗盡時再 consume() 拋 RetryBudgetExhaustedError
  - 模擬 LLMGateway retry 3次 + Execution retry 5次，總計不超過 10
"""

# ── 角色分工定義（從 knowledge/roles/ 動態載入）──────────
ROLES = _load_roles()

AGGREGATOR_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"

def build_prompt(role):
    """根據角色生成專屬 prompt"""
    return f"""你是一位資深系統架構師，正在 Code Review 以下系統設計規格。

{SPEC}

你的分工：{role['focus_desc']}

請以你主責的欄位為主，輸出完整 JSON。其他欄位若有值得提出的觀察可少量補充，沒有則留空陣列。
JSON 格式：
{{
  "risks": [{{"level": "high/medium/low", "issue": "...", "suggestion": "..."}}],
  "missing": [{{"item": "...", "reason": "...", "how": "..."}}],
  "improvements": [{{"area": "...", "current": "...", "better": "..."}}],
  "good_points": ["..."],
  "verdict": "你的整體評估"
}}

請只輸出 JSON，不要任何說明文字。"""

def get_content(response):
    msg = response.choices[0].message
    content = msg.content or getattr(msg, "reasoning_content", None)
    if content and "```" in content:
        # 取出 JSON 區塊
        for fence in ["```json", "```"]:
            if fence in content:
                start = content.find(fence) + len(fence)
                end   = content.rfind("```")
                if end > start:
                    return content[start:end].strip()
    return content

def parse_json(text):
    if text is None:
        return None, "無內容"
    try:
        # 清除可能的前綴雜訊
        text = text.strip()
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end]), None
        return None, "找不到 JSON"
    except Exception as e:
        return None, str(e)

def normalize(data):
    """確保每位專家回傳的 JSON 結構一致，防止 merge 時 KeyError/TypeError"""
    if not data:
        return {
            "risks": [],
            "missing": [],
            "improvements": [],
            "good_points": [],
            "verdict": ""
        }
    return {
        "risks": data.get("risks", []),
        "missing": data.get("missing", []),
        "improvements": data.get("improvements", []),
        "good_points": data.get("good_points", []),
        "verdict": data.get("verdict", "")
    }

def is_valid_output(data):
    """檢查 Aggregator 輸出是否符合預期結構（防止「成功但亂輸出」）"""
    if not data:
        return False
    return (
        isinstance(data.get("risks", []), list) and
        isinstance(data.get("missing", []), list) and
        isinstance(data.get("improvements", []), list)
    )

def main():
    results = {}
    total = len(ROLES)

    print("=" * 60)
    print(f"RequestRetryBudget 架構審查（角色分工），共 {total} 位專家 + 1 Aggregator")
    print("=" * 60)

    # ── Phase 1: 各專家分工審查 ──────────────────────────
    for i, role in enumerate(ROLES, 1):
        print(f"\n[{i}/{total}] {role['name']} ({role['id'].split('/')[-1]})")
        print("-" * 60)

        start = time.time()
        success = False
        last_error = None
        
        # 重試機制：最多重試 2 次，間隔 5 秒
        for attempt in range(3):  # 1 次原始嘗試 + 2 次重試
            try:
                if attempt > 0:
                    print(f"  重試 {attempt}/2...")
                    time.sleep(float(os.environ.get('RETRY_SLEEP', '5')))
                
                response = get_client().chat.completions.create(
                    model=role["id"],
                    messages=[
                        {"role": "system", "content": role["system"]},
                        {"role": "user",   "content": build_prompt(role)}
                    ],
                    temperature=0.3,
                    max_tokens=2048
                )
                elapsed = time.time() - start
                raw     = get_content(response)
                data, err = parse_json(raw)

                results[role["name"]] = {
                    "data": data, "raw": raw,
                    "time": elapsed, "error": err
                }

                if data:
                    fields = ", ".join(f"{k}:{len(v) if isinstance(v, list) else '✓'}" for k, v in data.items() if k != "verdict")
                    print(f"✅ {elapsed:.1f}s | {fields}")
                    print(f"   verdict: {data.get('verdict','')[:80]}...")
                    success = True
                else:
                    print(f"⚠️  {elapsed:.1f}s | JSON 解析失敗：{err}")
                    print(f"   raw: {str(raw)[:100]}")
                    last_error = err
                    
                break  # 成功執行（無論 JSON 是否解析成功）
                    
            except Exception as e:
                elapsed = time.time() - start
                last_error = str(e)
                if attempt < 2:  # 還沒到最後一次重試
                    continue  # 繼續重試
                else:  # 最終於失敗
                    results[role["name"]] = {"data": None, "time": elapsed, "error": str(e)}
                    print(f"❌ {elapsed:.1f}s | {e}")
                    success = False
        
        if not success and last_error:
            # 重試後仍失敗，記錄錯誤
            if role["name"] not in results:
                results[role["name"]] = {"data": None, "time": time.time() - start, "error": last_error}

    # ── Phase 2: 合併各專家結果 ────────────────────────────
    print(f"\n{'=' * 60}")
    print("合併各專家結果 → 送交 Aggregator")
    print("=" * 60)

    merged = {
        "risks": [],
        "missing": [],
        "improvements": [],
        "good_points": [],
        "expert_verdicts": {}
    }
    for name, r in results.items():
        d = normalize(r["data"])
        merged["risks"].extend(d["risks"])
        merged["missing"].extend(d["missing"])
        merged["improvements"].extend(d["improvements"])
        merged["good_points"].extend(d["good_points"])
        if d["verdict"]:
            merged["expert_verdicts"][name] = d["verdict"]

    ok_count = sum(1 for r in results.values() if r["data"])
    print(f"成功接收：{ok_count}/{total} 位專家")
    print(f"合併結果 keys：{list(merged.keys())}")

    # ── Phase 3: Aggregator 最終裁決 ──────────────────────
    print(f"\n{'=' * 60}")
    print(f"Aggregator ({AGGREGATOR_MODEL.split('/')[-1]}) 最終裁決")
    print("=" * 60)

    agg_prompt = f"""你是最終裁決者。以下是三位專家的分工審查結果：

    {json.dumps(merged, ensure_ascii=False, indent=2)}

    任務：
    1. 合併語意相同的項目（即使措辭不同）
    2. 刪除低價值或重複建議
    3. 對 risks / missing / improvements 排「優先順序」（最重要在前）
    4. 若專家意見衝突，請選擇你認為正確的，並在 verdict 說明原因

    限制：
    - 最多保留每類 5 條
    - 必須做取捨，不可全部保留

    輸出格式（只輸出 JSON）：
    {{
      "risks": [{{
        "level": "high/medium/low",
        "issue": "問題描述",
        "suggestion": "具體建議"
      }}],
      "missing": [{{
        "item": "缺少的設計",
        "reason": "為什麼需要",
        "how": "如何補充"
      }}],
      "improvements": [{{
        "area": "改善領域",
        "current": "現況",
        "better": "更好的做法"
      }}],
      "good_points": ["值得保留的設計決策"],
      "verdict": "整體評估（含衝突裁決說明）"
    }}"""

    agg_start = time.time()
    try:
        agg_response = get_client().chat.completions.create(
            model=AGGREGATOR_MODEL,
            messages=[
                {"role": "system", "content": "你是資深首席架構師，負責整合各專家意見並做最終裁決。只輸出 JSON，不要任何說明文字。"},
                {"role": "user",   "content": agg_prompt}
            ],
            temperature=0.2,
            max_tokens=4096
        )
        agg_elapsed = time.time() - agg_start
        agg_raw  = get_content(agg_response)
        agg_data, agg_err = parse_json(agg_raw)

        if agg_data:
            print(f"✅ {agg_elapsed:.1f}s | Aggregator 裁決完成")
            print(f"   risks:{len(agg_data.get('risks',[]))} missing:{len(agg_data.get('missing',[]))} improvements:{len(agg_data.get('improvements',[]))}")
        else:
            print(f"⚠️  {agg_elapsed:.1f}s | Aggregator JSON 解析失敗：{agg_err}")

    except Exception as e:
        agg_elapsed = time.time() - agg_start
        print(f"❌ {agg_elapsed:.1f}s | Aggregator 失敗：{e}")
        agg_data = None

    # Sanity check：即使 JSON 解析成功，也要檢查結構是否正確
    if is_valid_output(agg_data):
        final = agg_data
        print("✅ Aggregator 輸出通過 sanity check")
    else:
        final = merged
        print("⚠️  Aggregator 輸出未通過 sanity check，fallback 到合併結果")

    # ── 最終輸出 ────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("最終裁決報告（JSON）：")
    print("=" * 60)
    print(json.dumps(final, ensure_ascii=False, indent=2))

    # 各專家摘要
    print(f"\n{'=' * 60}")
    print("各專家執行摘要：")
    print("=" * 60)
    for name, r in results.items():
        status = "✅" if r["data"] else "❌"
        print(f"  {status} {name}: {r['time']:.1f}s | {r.get('error') or 'OK'}")
    print(f"  🏛️  Aggregator: {agg_elapsed:.1f}s")
    total_time = sum(r["time"] for r in results.values()) + agg_elapsed
    print(f"  ⏱️  總耗時：{total_time:.1f}s（{total + 1} 次 API 呼叫）")

    print(f"\n{'=' * 60}")
    print("完成！最終報告已由 Aggregator 整合裁決。")
    print("=" * 60)
if __name__ == '__main__':
    main()


def review_project(specification: str) -> Dict:
    load_roles = _load_roles
    """
    審查專案規格
    
    Args:
        specification: 專案規格說明文字
        
    Returns:
        Dict: 審查結果 JSON
    """
    import sys
    from io import StringIO
    import json
    
    # 暫時攔截 stdout
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # 載入角色
        ROLES = load_roles()
        AGGREGATOR_MODEL = "nvidia/llama-3.1-nemotron-ultra-253b-v1"
        
        results = {}
        
        # Phase 1: 各專家分工審查
        for role in ROLES:
            try:
                # 直接使用 specification 作為 prompt
                prompt = f"""你是一位資深系統架構師，正在 Code Review 以下系統設計規格。

{specification}

你的分工：{role['focus_desc']}

請以你主責的欄位為主，輸出完整 JSON。其他欄位若有值得提出的觀察可少量補充，沒有則留空陣列。
JSON 格式：
{{
  "risks": [{{"level": "high/medium/low", "issue": "...", "suggestion": "..."}}],
  "missing": [{{"item": "...", "reason": "...", "how": "..."}}],
  "improvements": [{{"area": "...", "current": "...", "better": "..."}}],
  "good_points": ["..."],
  "verdict": "你的整體評估"
}}

請只輸出 JSON，不要任何說明文字。"""
                
                response = get_client().chat.completions.create(
                    model=role["id"],
                    messages=[
                        {"role": "system", "content": role["system"]},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2048
                )
                raw = get_content(response)
                data, err = parse_json(raw)
                results[role["name"]] = normalize(data)
            except Exception as e:
                import json as json_module
                from datetime import datetime, timezone
                log_entry = {
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0800"),
                    "lvl": "ERROR",
                    "script": "loader.py",
                    "fn": "review_project",
                    "msg": f"專家 {role['name']} 審查失敗：{e}",
                    "extra": {"role_name": role['name'], "error": str(e)},
                    "elapsed_ms": 0
                }
                print(json_module.dumps(log_entry, ensure_ascii=False))
                results[role["name"]] = normalize(None)
        
        # Phase 2: 合併各專家結果
        merged = {
            "risks": [],
            "missing": [],
            "improvements": [],
            "good_points": [],
            "expert_verdicts": {}
        }
        for name, r in results.items():
            merged["risks"].extend(r["risks"])
            merged["missing"].extend(r["missing"])
            merged["improvements"].extend(r["improvements"])
            merged["good_points"].extend(r["good_points"])
            if r["verdict"]:
                merged["expert_verdicts"][name] = r["verdict"]
        
        # Phase 3: Aggregator 最終裁決
        agg_prompt = f"""你是最終裁決者。以下是三位專家的分工審查結果：

        {json.dumps(merged, ensure_ascii=False, indent=2)}

        任務：
        1. 合併語意相同的項目
        2. 刪除低價值或重複建議
        3. 對 risks / missing / improvements 排「優先順序」
        4. 若專家意見衝突，請選擇你認為正確的

        限制：
        - 最多保留每類 5 條
        - 必須做取捨

        輸出格式（只輸出 JSON）：
        {{
          "risks": [{{
            "level": "high/medium/low",
            "issue": "問題描述",
            "suggestion": "具體建議"
          }}],
          "missing": [{{
            "item": "缺少的設計",
            "reason": "為什麼需要",
            "how": "如何補充"
          }}],
          "improvements": [{{
            "area": "改善領域",
            "current": "現況",
            "better": "更好的做法"
          }}],
          "good_points": ["值得保留的設計決策"],
          "verdict": "整體評估"
        }}"""
        
        try:
            agg_response = get_client().chat.completions.create(
                model=AGGREGATOR_MODEL,
                messages=[
                    {"role": "system", "content": "你是資深首席架構師，負責整合各專家意見並做最終裁決。只輸出 JSON，不要任何說明文字。"},
                    {"role": "user", "content": agg_prompt}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            agg_raw = get_content(agg_response)
            agg_data, agg_err = parse_json(agg_raw)
            
            if is_valid_output(agg_data):
                final_result = agg_data
            else:
                final_result = merged
        except Exception as e:
            print(f"Aggregator 失敗：{e}")
            final_result = merged
        
        return final_result
        
    finally:
        sys.stdout = old_stdout


if __name__ == "__main__":
    # 測試用
    print("測試載入角色...")
    roles = load_roles()
    print(f"成功載入 {len(roles)} 個角色:")
    for role in roles:
        print(f"  - {role['name']} ({role['id']})")
