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
        print(f"⚠️  警告：找不到角色檔案 {role_path}，使用內建預設值")
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
        print(f"⚠️  警告：角色檔案 JSON 格式錯誤 {e}，使用內建預設值")
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
        print(f"⚠️  警告：找不到 roles 目錄 {roles_dir}，使用內建預設值")
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
            print(f"⚠️  載入 {filename} 失敗：{e}")
    
    if not roles:
        print("⚠️  所有角色載入失敗，使用內建預設值")
        return BUILTIN_ROLES
    
    return roles


if __name__ == "__main__":
    # 測試用
    print("測試載入角色...")
    roles = load_roles()
    print(f"成功載入 {len(roles)} 個角色:")
    for role in roles:
        print(f"  - {role['name']} ({role['id']})")
