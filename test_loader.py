"""
測試 engine/loader.py 模組

涵蓋：
- load_roles() 成功與 fallback 情境
- save_role() 與 load_role() 迴圈
- load_standards() 空目錄情境
- save_risk_template() 儲存與載入
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from engine.loader import (
    load_roles, 
    load_role, 
    save_role, 
    load_standards, 
    load_risk_templates, 
    save_risk_template,
    get_knowledge_base_path,
    BUILTIN_ROLES
)


@pytest.fixture
def temp_knowledge_base():
    """建立暫時的 knowledge/ 目錄用於測試"""
    # 建立暫時目錄
    temp_dir = tempfile.mkdtemp()
    kb_path = Path(temp_dir) / "knowledge"
    kb_path.mkdir(parents=True, exist_ok=True)
    
    # 建立子目錄
    roles_dir = kb_path / "roles"
    roles_dir.mkdir(exist_ok=True)
    
    standards_dir = kb_path / "standards"
    standards_dir.mkdir(exist_ok=True)
    
    templates_dir = kb_path / "risk_templates"
    templates_dir.mkdir(exist_ok=True)
    
    # 複製現有角色檔案（如果存在）
    original_roles = Path(__file__).parent / "knowledge" / "roles"
    if original_roles.exists():
        for role_file in original_roles.glob("*.json"):
            shutil.copy2(role_file, roles_dir / role_file.name)
    
    yield kb_path
    
    # 清理暫存目錄
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_knowledge_base(monkeypatch, temp_knowledge_base):
    """Mock get_knowledge_base_path() 回傳暫時目錄"""
    def mock_get_path():
        return temp_knowledge_base
    
    monkeypatch.setattr("engine.loader.get_knowledge_base_path", mock_get_path)
    return temp_knowledge_base


class TestLoadRoles:
    """測試 load_roles() 函數"""
    
    def test_load_roles_success(self, mock_knowledge_base):
        """測試成功載入 roles"""
        roles = load_roles()
        
        # 應該載入至少 3 個角色
        assert len(roles) >= 3
        
        # 確認是從檔案載入，不是 BUILTIN_ROLES 本身
        assert roles is not BUILTIN_ROLES
        
        # 每個角色應有基本欄位
        for role in roles:
            assert "id" in role
            assert "name" in role
            assert "system" in role
            assert isinstance(role["id"], str)
            assert isinstance(role["name"], str)
            assert isinstance(role["system"], str)
    
    def test_load_roles_fallback(self, monkeypatch):
        """測試載入失敗時的 fallback 機制"""
        # Mock get_knowledge_base_path 回傳不存在的目錄
        def mock_get_path():
            return Path("/nonexistent/knowledge")
        
        monkeypatch.setattr("engine.loader.get_knowledge_base_path", mock_get_path)
        
        # 應該回退到內建角色，不會拋出異常
        roles = load_roles()
        
        # 內建有 3 個角色
        assert len(roles) == 3
        assert roles[0]["name"] == "Risk-Analyst"
        assert roles[1]["name"] == "Completeness-Reviewer"
        assert roles[2]["name"] == "Improvement-Advisor"


class TestSaveAndLoadRole:
    """測試 save_role() 與 load_role() 迴圈"""
    
    def test_save_and_load_role(self, mock_knowledge_base):
        """測試 save_role + load_role 迴圈"""
        # 準備測試資料
        test_role = {
            "id": "test/test-model",
            "name": "Test-Role",
            "system": "這是一個測試角色",
            "focus_fields": ["risks"],
            "focus_desc": "測試用途"
        }
        
        filename = "test_role.json"
        
        # 儲存角色
        saved_path = save_role(filename, test_role)
        
        # 驗證檔案存在
        assert saved_path.exists()
        assert saved_path.name == filename
        
        # 載入角色
        loaded_role = load_role(filename)
        
        # 驗證內容正確
        assert loaded_role["id"] == test_role["id"]
        assert loaded_role["name"] == test_role["name"]
        assert loaded_role["system"] == test_role["system"]
        assert loaded_role["focus_fields"] == test_role["focus_fields"]
        assert loaded_role["focus_desc"] == test_role["focus_desc"]
    
    def test_save_role_invalid_filename(self, mock_knowledge_base):
        """測試 save_role 拒絕無效的檔案名稱"""
        test_role = {"id": "test", "name": "Test", "system": "Test"}
        
        # 副檔名不是 .json 應該拋出 ValueError
        with pytest.raises(ValueError, match=".json"):
            save_role("test_role.txt", test_role)


class TestLoadStandards:
    """測試 load_standards() 函數"""
    
    def test_load_standards_empty(self, mock_knowledge_base):
        """測試 standards 目錄為空的情況"""
        standards = load_standards()
        
        # 空目錄應該回傳空列表
        assert isinstance(standards, list)
        assert len(standards) == 0
    
    def test_load_standards_with_files(self, mock_knowledge_base):
        """測試載入規範檔案"""
        standards_dir = mock_knowledge_base / "standards"
        
        # 建立測試檔案
        test_content = "# 測試規範\n\n這是測試內容。"
        test_file = standards_dir / "test_standard.md"
        test_file.write_text(test_content, encoding='utf-8')
        
        # 載入規範
        standards = load_standards()
        
        # 驗證結果
        assert len(standards) == 1
        assert standards[0]["filename"] == "test_standard.md"
        assert standards[0]["content"] == test_content


class TestRiskTemplates:
    """測試 risk_templates 相關函數"""
    
    def test_save_risk_template(self, mock_knowledge_base):
        """測試風險模板的儲存與載入"""
        # 準備測試資料
        test_template = {
            "level": "high",
            "issue": "這是測試問題",
            "suggestion": "這是測試建議"
        }
        
        name = "test_template"
        
        # 儲存模板
        saved_path = save_risk_template(name, test_template)
        
        # 驗證檔案存在
        assert saved_path.exists()
        assert saved_path.name == f"{name}.json"
        
        # 載入所有模板
        templates = load_risk_templates()
        
        # 驗證結果
        assert len(templates) == 1
        assert templates[0]["filename"] == f"{name}.json"
        
        loaded_data = templates[0]["data"]
        assert loaded_data["level"] == test_template["level"]
        assert loaded_data["issue"] == test_template["issue"]
        assert loaded_data["suggestion"] == test_template["suggestion"]
    
    def test_save_risk_template_invalid_name(self, mock_knowledge_base):
        """測試 save_risk_template 拒絕無效的名稱"""
        test_template = {"level": "high", "issue": "Test", "suggestion": "Test"}
        
        # 空名稱應該拋出 ValueError
        with pytest.raises(ValueError, match="invalid|無效"):
            save_risk_template("", test_template)
        
        # 包含路徑分隔符應該拋出 ValueError
        with pytest.raises(ValueError, match="invalid|無效"):
            save_risk_template("test/template", test_template)
    
    def test_save_risk_template_missing_fields(self, mock_knowledge_base):
        """測試 save_risk_template 拒絕缺少必要欄位的資料"""
        incomplete_template = {
            "level": "high",
            # 缺少 issue 和 suggestion
        }
        
        with pytest.raises(ValueError, match="issue|suggestion|缺少"):
            save_risk_template("incomplete", incomplete_template)
    
    def test_load_risk_templates_empty(self, mock_knowledge_base):
        """測試空 templates 目錄"""
        templates = load_risk_templates()
        
        # 空目錄應該回傳空列表
        assert isinstance(templates, list)
        assert len(templates) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
