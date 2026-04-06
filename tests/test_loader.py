import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import MagicMock, patch
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
from design_decision_engine import review_project


@pytest.fixture
def temp_knowledge_base():
    """建立暫時的 knowledge/ 目錄用於測試"""
    temp_dir = tempfile.mkdtemp()
    kb_path = Path(temp_dir) / "knowledge"
    kb_path.mkdir(parents=True, exist_ok=True)
    
    # 建立子目錄
    (kb_path / "roles").mkdir(exist_ok=True)
    (kb_path / "standards").mkdir(exist_ok=True)
    (kb_path / "risk_templates").mkdir(exist_ok=True)
    
    yield kb_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_kb_path(monkeypatch, temp_knowledge_base):
    """Mock get_knowledge_base_path() 回傳暫時目錄"""
    monkeypatch.setattr("engine.loader.get_knowledge_base_path", lambda: temp_knowledge_base)
    return temp_knowledge_base


class TestKnowledgeBasePath:
    """測試 get_knowledge_base_path()"""
    
    def test_get_path_not_found(self, monkeypatch):
        """測試找不到目錄時拋出錯誤"""
        # Mock Path.resolve to return a path not in 'engine'
        monkeypatch.setattr(Path, "resolve", lambda self: Path("/tmp/fake/file.py"))
        
        # Mock Path.exists to always return False for 'knowledge'
        original_exists = Path.exists
        def mock_exists(self):
            if self.name == "knowledge":
                return False
            return original_exists(self)
    
        monkeypatch.setattr(Path, "exists", mock_exists)
        with pytest.raises(FileNotFoundError, match="找不到 knowledge"):
            get_knowledge_base_path()


class TestLoadRoles:
    """測試角色載入"""
    
    def test_load_roles_success(self, mock_kb_path):
        # 建立一個測試角色
        save_role("risk_analyst.json", BUILTIN_ROLES[0])
        save_role("completeness_reviewer.json", BUILTIN_ROLES[1])
        save_role("improvement_advisor.json", BUILTIN_ROLES[2])
        
        roles = load_roles()
        assert len(roles) == 3
    
    def test_load_role_not_found_fallback(self, mock_kb_path):
        """測試單個檔案不存在時回退"""
        role = load_role("risk_analyst.json")
        assert role == BUILTIN_ROLES[0]

    def test_load_role_invalid_json_fallback(self, mock_kb_path):
        """測試 JSON 格式錯誤時回退"""
        role_path = mock_kb_path / "roles" / "risk_analyst.json"
        role_path.write_text("invalid json", encoding='utf-8')
        
        role = load_role("risk_analyst.json")
        assert role == BUILTIN_ROLES[0]

    def test_load_roles_dir_not_exists_fallback(self, monkeypatch):
        """測試目錄不存在時回退"""
        monkeypatch.setattr("engine.loader.get_knowledge_base_path", lambda: Path("/tmp/nowhere"))
        roles = load_roles()
        assert roles == BUILTIN_ROLES


class TestStandards:
    """測試規範載入"""
    
    def test_load_standards_empty(self, mock_kb_path):
        assert load_standards() == []

    def test_load_standards_error(self, mock_kb_path, monkeypatch):
        """測試讀取失敗路徑"""
        (mock_kb_path / "standards" / "bad.md").write_text("test", encoding='utf-8')
        # Mock open to fail
        def mock_open(*args, **kwargs):
            raise Exception("Read error")
        
        with patch("builtins.open", side_effect=mock_open):
            assert load_standards() == []


class TestRiskTemplates:
    """測試風險模板"""
    
    def test_save_and_load_success(self, mock_kb_path):
        data = {"level": "low", "issue": "x", "suggestion": "y"}
        save_risk_template("test", data)
        temps = load_risk_templates()
        assert len(temps) == 1
        assert temps[0]["data"] == data

    def test_load_templates_error(self, mock_kb_path):
        (mock_kb_path / "risk_templates" / "bad.json").write_text("invalid", encoding='utf-8')
        assert load_risk_templates() == []


class TestReviewProject:
    """測試 review_project 審查引擎"""
    
    def test_review_project_full_flow(self, mock_openai, mock_kb_path):
        """測試完整的專家 + Aggregator 流程"""
        # 準備 Mock 回傳值
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '{"risks": [{"level": "high", "issue": "T1"}], "verdict": "V"}'
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # 模擬 3 位專家 + 1 位 Aggregator 的呼叫
        mock_openai.chat.completions.create.return_value = mock_response
        
        result = review_project("這是測試規格")
        
        assert "risks" in result
        assert len(result["risks"]) > 0
        assert mock_openai.chat.completions.create.call_count >= 1

    def test_load_roles_json_error(self, mock_kb_path):
        """測試 JSON 解析失敗時回退"""
        role_path = mock_kb_path / "roles" / "err.json"
        role_path.write_text("invalid{json", encoding='utf-8')
        roles = load_roles()
        # Should still contain built-in roles
        assert len(roles) >= len(BUILTIN_ROLES)

    def test_load_standards_with_files(self, mock_kb_path):
        """測試成功讀取規範"""
        (mock_kb_path / "standards" / "s1.md").write_text("rule 1", encoding='utf-8')
        standards = load_standards()
        assert len(standards) == 1
        assert "rule 1" in standards[0]["content"]

    def test_load_risk_templates_json_error(self, mock_kb_path):
        """測試風險模板 JSON 錯誤"""
        (mock_kb_path / "risk_templates" / "err.json").write_text("invalid", encoding='utf-8')
        temps = load_risk_templates()
        assert len(temps) == 0
