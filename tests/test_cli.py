import pytest
from unittest.mock import MagicMock, patch
import cli
from pathlib import Path

@pytest.fixture
def mock_console():
    with patch("cli.console") as mock:
        yield mock

@pytest.fixture
def mock_questionary():
    with patch("questionary.select") as mock_select, \
         patch("questionary.text") as mock_text, \
         patch("questionary.confirm") as mock_confirm:
        yield mock_select, mock_text, mock_confirm

def test_show_main_menu(mock_questionary):
    mock_select, _, _ = mock_questionary
    mock_select.return_value.ask.return_value = "1"
    assert cli.show_main_menu() == "1"

def test_add_new_review_success(mock_questionary, mock_console):
    _, mock_text, mock_confirm = mock_questionary
    mock_text.return_value.ask.return_value = "Test Project"
    mock_confirm.return_value.ask.return_value = True
    
    with patch("cli.run_design_review", return_value={"risks": []}), \
         patch("cli.save_review") as mock_save:
        cli.add_new_review()
        assert mock_save.called
        # Check if any call contains the success message
        # The success message might be in a string or Panel
        found = False
        for call in mock_console.print.call_args_list:
            arg = str(call[0][0])
            if "✅ 審查完成" in arg:
                found = True
        assert found

def test_add_new_review_empty_name(mock_questionary, mock_console):
    _, mock_text, _ = mock_questionary
    mock_text.return_value.ask.return_value = ""
    cli.add_new_review()
    # Similar check for error message
    found = False
    for call in mock_console.print.call_args_list:
        arg = str(call[0][0])
        if "❌ 專案名稱不能為空" in arg:
            found = True
    assert found

def test_run_design_review(mock_openai):
    # This calls get_client().chat.completions.create
    # mock_openai is from conftest.py
    with patch("cli.load_roles", return_value=[{"name": "E1", "id": "model-1", "system": "s"}]), \
         patch("cli.get_client", return_value=mock_openai):
        result = cli.run_design_review("Spec")
        assert "risks" in result

def test_view_history(mock_console):
    mock_rows = [(1, "P1", "2024-01-01 10:00:00", 1, 0, 0, "Verdict")]
    with patch("cli.get_recent_reviews", return_value=mock_rows):
        cli.view_history()
        # Verify Table was printed
        from rich.table import Table
        assert any(isinstance(call[0][0], Table) for call in mock_console.print.call_args_list)

def test_manage_knowledge_base_loop(mock_questionary):
    mock_select, _, _ = mock_questionary
    # First call returns "b" (back)
    mock_select.return_value.ask.return_value = "b"
    cli.manage_knowledge_base()
    assert mock_select.called

def test_view_all_roles(mock_console):
    with patch("cli.load_roles", return_value=[{"name": "E1", "id": "m1", "system": "s"}]):
        cli.view_all_roles()
        # The first print call might be a Panel, the later ones strings
        found = False
        for call in mock_console.print.call_args_list:
            arg = str(call[0][0])
            if "E1" in arg:
                found = True
        assert found

def test_edit_role_prompt_success(mock_questionary, mock_console):
    mock_select, mock_text, mock_confirm = mock_questionary
    mock_select.return_value.ask.return_value = "1. E1 (m1)"
    mock_confirm.return_value.ask.side_effect = [False, True] # Backup: No, Confirm: Yes
    mock_text.return_value.ask.return_value = "New Prompt"
    
    with patch("cli.load_roles", return_value=[{"name": "E1", "id": "m1", "system": "s"}]), \
         patch("cli.save_role") as mock_save:
        cli.edit_role_prompt()
        assert mock_save.called
        found = False
        for call in mock_console.print.call_args_list:
            arg = str(call[0][0])
            if "✅ 成功更新" in arg:
                found = True
        assert found

def test_import_design_standard_success(mock_questionary, mock_console, tmp_path):
    mock_select, mock_text, mock_confirm = mock_questionary
    mock_select.return_value.ask.return_value = ".md"
    
    # Create fake source file
    src = tmp_path / "test.md"
    src.write_text("content", encoding='utf-8')
    
    # Provide the source file path as input
    mock_text.return_value.ask.return_value = str(src)
    
    mock_confirm.return_value.ask.return_value = True # In case destination exists
    
    with patch("shutil.copy2"):
        cli.import_design_standard()
        found = False
        for call in mock_console.print.call_args_list:
            arg = str(call[0][0])
            if "✅ 成功匯入" in arg:
                found = True
        assert found


def test_view_risk_templates(mock_console):
    with patch("cli.load_risk_templates", return_value=[{"filename": "t.json", "data": {}}]):
        cli.view_risk_templates()
        assert "t.json" in mock_console.print.call_args_list[1][0][0]

def test_add_new_risk_template_success(mock_questionary, mock_console):
    mock_select, mock_text, _ = mock_questionary
    mock_select.return_value.ask.return_value = "high"
    mock_text.return_value.ask.side_effect = ["Issue", "Suggestion", "template_name"]
    
    with patch("cli.save_risk_template", return_value=Path("t.json")):
        cli.add_new_risk_template()
        assert "✅ 成功儲存" in mock_console.print.call_args[0][0]

def test_cli_main_loop(mock_questionary):
    # Mock main_menu to return "q" immediately
    with patch("cli.show_main_menu", return_value="q"):
        cli.main()
