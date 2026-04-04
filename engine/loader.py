"""
知識庫載入模組

負責從 knowledge/ 目錄載入角色設定，
提供 fallback 機制確保系統穩定性。
"""

import json
from pathlib import Path
from typing import List, Dict


# 內建 fallback roles（與 design_decision_engine.py 中的 ROLES 完全相同）
BUILTIN_ROLES = [
    {
        "id": "deepseek-ai/deepseek-v3.2",
        "name": "Risk-Analyst",
        "system": "你是專精安全性與風險分析的資深架構師。請只輸出 JSON，不要任何說明文字。",
        "focus_fields": ["risks", "verdict"],
        "focus_desc": "主責 risks（含 level/issue/suggestion），若審查中發現重要的 missing 或 improvements 也可少量補充",
    },
    {
        "id": "qwen/qwen3.5-397b-a17b",
        "name": "Completeness-Reviewer",
        "system": "你是專精需求完整性檢查的資深架構師。請只輸出 JSON，不要任何說明文字。",
        "focus_fields": ["missing", "verdict"],
        "focus_desc": "主責 missing（含 item/reason/how），若審查中發現重要的 risks 或 improvements 也可少量補充",
    },
    {
        "id": "mistralai/mistral-large-3-675b-instruct-2512",
        "name": "Improvement-Advisor",
        "system": "你是專精架構改善建議的資深架構師。請只輸出 JSON，不要任何說明文字。",
        "focus_fields": ["improvements", "good_points", "verdict"],
        "focus_desc": "主責 improvements（含 area/current/better）與 good_points，若審查中發現重要的 risks 或 missing 也可少量補充",
    },
]


def get_knowledge_base_path() -> Path:
    """
    取得 knowledge/ 目錄的絕對路徑
    
    Returns:
        Path: knowledge/ 目錄的絕對路徑
        
    Raises:
        FileNotFoundError: 若找不到 knowledge/ 目錄
    """
    current = Path(__file__).resolve()
    
    # 若在 engine/loader.py
    if current.parent.name == "engine":
        return current.parent.parent / "knowledge"
    
    # 若在 cli.py 或其他位置呼叫
    for parent in current.parents:
        if (parent / "knowledge").exists():
            return parent / "knowledge"
    
    raise FileNotFoundError("找不到 knowledge/ 目錄")


def load_role(filename: str) -> Dict:
    """
    載入單個角色檔案
    
    Args:
        filename: 檔案名稱（不含路徑），例如 'risk_analyst.json'
        
    Returns:
        Dict: 角色設定
        
    Raises:
        ValueError: 若檔案無法識別且無 fallback
    """
    role_path = get_knowledge_base_path() / "roles" / filename
    
    try:
        with open(role_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_role",
            "msg": f"警告：找不到角色檔案 {role_path}，使用內建預設值",
            "extra": {"filename": filename},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        # 根據 filename 回傳對應的內建角色
        if filename == "risk_analyst.json":
            return BUILTIN_ROLES[0]
        elif filename == "completeness_reviewer.json":
            return BUILTIN_ROLES[1]
        elif filename == "improvement_advisor.json":
            return BUILTIN_ROLES[2]
        else:
            raise ValueError(f"未知的角色檔案：{filename}")
    except json.JSONDecodeError as e:
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_role",
            "msg": f"警告：角色檔案 JSON 格式錯誤 {e}，使用內建預設值",
            "extra": {"filename": filename, "error": str(e)},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        if filename == "risk_analyst.json":
            return BUILTIN_ROLES[0]
        elif filename == "completeness_reviewer.json":
            return BUILTIN_ROLES[1]
        elif filename == "improvement_advisor.json":
            return BUILTIN_ROLES[2]
        else:
            return BUILTIN_ROLES[0]


def load_roles() -> List[Dict]:
    """
    從 knowledge/roles/ 載入所有角色
    
    Returns:
        List[Dict]: 角色設定列表
        
    Fallback:
        若載入失敗，回退到內建的 ROLES 常數
    """
    roles_dir = get_knowledge_base_path() / "roles"
    
    if not roles_dir.exists():
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_roles",
            "msg": f"警告：找不到 roles 目錄 {roles_dir}，使用內建預設值",
            "extra": {"roles_dir": str(roles_dir)},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        return BUILTIN_ROLES
    
    role_files = [
        "risk_analyst.json",
        "completeness_reviewer.json",
        "improvement_advisor.json"
    ]
    
    roles = []
    for filename in role_files:
        try:
            role = load_role(filename)
            roles.append(role)
        except Exception as e:
            import json as json_module
            from datetime import datetime
            log_entry = {
                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "lvl": "WARN",
                "script": "loader.py",
                "fn": "load_roles",
                "msg": f"載入 {filename} 失敗：{e}",
                "extra": {"filename": filename, "error": str(e)},
                "elapsed_ms": 0
            }
            print(json_module.dumps(log_entry, ensure_ascii=False))
    
    if not roles:
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_roles",
            "msg": "所有角色載入失敗，使用內建預設值",
            "extra": {},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        return BUILTIN_ROLES
    
    return roles


def save_role(filename: str, data: Dict) -> Path:
    """
    儲存角色設定至 knowledge/roles/
    
    Args:
        filename: 檔案名稱（不含路徑），例如 'risk_analyst.json'
        data: 角色設定字典
        
    Returns:
        Path: 儲存的檔案路徑
        
    Raises:
        ValueError: 若檔案名稱無效
    """
    if not filename.endswith('.json'):
        raise ValueError("角色檔案必須以 .json 結尾")
    
    roles_dir = get_knowledge_base_path() / "roles"
    role_path = roles_dir / filename
    
    # 確保目錄存在
    roles_dir.mkdir(parents=True, exist_ok=True)
    
    # 寫入 JSON
    with open(role_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return role_path


def load_standards() -> List[Dict[str, str]]:
    """
    讀取 knowledge/standards/ 所有 .md/.txt 檔案
    
    Returns:
        List[Dict]: 規範列表，每個元素包含 {'filename': str, 'content': str}
    """
    standards_dir = get_knowledge_base_path() / "standards"
    
    if not standards_dir.exists():
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_standards",
            "msg": f"警告：找不到 standards 目錄 {standards_dir}",
            "extra": {"standards_dir": str(standards_dir)},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        return []
    
    standards = []
    # 分別處理 .md 和 .txt 檔案（避免 glob pattern 相容性問題）
    for pattern in ["*.md", "*.txt"]:
        for file_path in standards_dir.glob(pattern):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    standards.append({
                        'filename': file_path.name,
                        'content': content
                    })
            except Exception as e:
                import json as json_module
                from datetime import datetime
                log_entry = {
                    "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
                    "lvl": "WARN",
                    "script": "loader.py",
                    "fn": "load_standards",
                    "msg": f"讀取規範檔案 {file_path.name} 失敗：{e}",
                    "extra": {"filename": file_path.name, "error": str(e)},
                    "elapsed_ms": 0
                }
                print(json_module.dumps(log_entry, ensure_ascii=False))
    
    return standards


def load_risk_templates() -> List[Dict]:
    """
    讀取 knowledge/risk_templates/ 所有 .json 檔案
    
    Returns:
        List[Dict]: 風險模板列表，每個元素包含 {'filename': str, 'data': Dict}
    """
    templates_dir = get_knowledge_base_path() / "risk_templates"
    
    if not templates_dir.exists():
        import json as json_module
        from datetime import datetime
        log_entry = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
            "lvl": "WARN",
            "script": "loader.py",
            "fn": "load_risk_templates",
            "msg": f"警告：找不到 risk_templates 目錄 {templates_dir}",
            "extra": {"templates_dir": str(templates_dir)},
            "elapsed_ms": 0
        }
        print(json_module.dumps(log_entry, ensure_ascii=False))
        return []
    
    templates = []
    for file_path in templates_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                templates.append({
                    'filename': file_path.name,
                    'data': data
                })
        except Exception as e:
            import json as json_module
            from datetime import datetime
            log_entry = {
                "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
                "lvl": "WARN",
                "script": "loader.py",
                "fn": "load_risk_templates",
                "msg": f"讀取風險模板 {file_path.name} 失敗：{e}",
                "extra": {"filename": file_path.name, "error": str(e)},
                "elapsed_ms": 0
            }
            print(json_module.dumps(log_entry, ensure_ascii=False))
    
    return templates


def save_risk_template(name: str, data: Dict) -> Path:
    """
    儲存風險模板至 knowledge/risk_templates/
    
    Args:
        name: 模板名稱（不含副檔名）
        data: 風險模板字典，應包含 level/issue/suggestion
        
    Returns:
        Path: 儲存的檔案路徑
        
    Raises:
        ValueError: 若模板名稱無效或資料結構不正確
    """
    if not name or '/' in name or '\\' in name:
        raise ValueError("無效的模板名稱")
    
    # 驗證基本結構
    required_keys = ['level', 'issue', 'suggestion']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"風險模板缺少必要欄位：{key}")
    
    templates_dir = get_knowledge_base_path() / "risk_templates"
    template_path = templates_dir / f"{name}.json"
    
    # 確保目錄存在
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # 寫入 JSON
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return template_path


def review_project(specification: str) -> Dict:
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
    from design_decision_engine import get_client, get_content, parse_json, normalize, is_valid_output
    from engine.loader import load_roles
    
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
                from datetime import datetime
                log_entry = {
                    "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+0800"),
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
