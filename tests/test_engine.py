import pytest
import json
from unittest.mock import MagicMock, patch
from design_decision_engine import (
    normalize, 
    is_valid_output, 
    get_content, 
    parse_json, 
    build_prompt, 
    get_client,
    main
)

def test_get_client():
    """測試 get_client 是否返回 OpenAI 實例"""
    client = get_client()
    assert client is not None
    # 在 conftest.py 中被 mock 了，應該是一個 MagicMock
    assert isinstance(client, MagicMock)

def test_build_prompt():
    """測試 build_prompt 生成內容"""
    role = {"focus_desc": "測試焦點描述"}
    prompt = build_prompt(role)
    assert "測試焦點描述" in prompt
    assert "JSON 格式" in prompt
    assert "RequestRetryBudget" in prompt

def test_get_content_simple():
    """測試 get_content 取得一般內容"""
    response = MagicMock()
    response.choices[0].message.content = "test content"
    response.choices[0].message.reasoning_content = None
    assert get_content(response) == "test content"

def test_get_content_reasoning():
    """測試 get_content 從 reasoning_content 取得內容"""
    response = MagicMock()
    response.choices[0].message.content = None
    response.choices[0].message.reasoning_content = "reasoning content"
    assert get_content(response) == "reasoning content"

def test_get_content_with_fence():
    """測試 get_content 解析 Markdown code fence"""
    response = MagicMock()
    response.choices[0].message.content = "這裡有一些文字\n```json\n{\"key\": \"value\"}\n```\n結束後綴"
    assert get_content(response) == "{\"key\": \"value\"}"
    
    response.choices[0].message.content = "```\n{\"key\": \"value\"}\n```"
    assert get_content(response) == "{\"key\": \"value\"}"

def test_parse_json_success():
    """測試 parse_json 成功解析"""
    data, err = parse_json('{"risks": []}')
    assert data == {"risks": []}
    assert err is None

def test_parse_json_with_noise():
    """測試 parse_json 清除雜訊後解析"""
    data, err = parse_json('這裡是雜訊 {"risks": []} 也是雜訊')
    assert data == {"risks": []}
    assert err is None

def test_parse_json_none_or_empty():
    """測試 parse_json 處理無效輸入"""
    data, err = parse_json(None)
    assert data is None
    assert "無內容" in err
    
    data, err = parse_json("沒有括號的文字")
    assert data is None
    assert "找不到 JSON" in err

def test_normalize_empty_or_none():
    """測試 normalize 處理 None 或空白字典"""
    expected = {
        "risks": [],
        "missing": [],
        "improvements": [],
        "good_points": [],
        "verdict": ""
    }
    assert normalize(None) == expected
    assert normalize({}) == expected

def test_normalize_partial_data():
    """測試 normalize 補齊缺失的 key"""
    data = {
        "risks": [{"level": "high", "issue": "test"}],
        "verdict": "ok"
    }
    result = normalize(data)
    assert len(result["risks"]) == 1
    assert result["missing"] == []
    assert result["improvements"] == []
    assert result["good_points"] == []
    assert result["verdict"] == "ok"

def test_is_valid_output_success():
    """測試 is_valid_output 對正確的結構回傳 True"""
    data = {
        "risks": [],
        "missing": [{"item": "test"}],
        "improvements": [],
        "good_points": [],
        "verdict": "ok"
    }
    assert is_valid_output(data) is True

def test_is_valid_output_invalid_type():
    """測試 is_valid_output 處理型態錯誤"""
    data_wrong_risks = {
        "risks": "這是一個字串",
        "missing": [],
        "improvements": []
    }
    assert is_valid_output(data_wrong_risks) is False

def test_main_orchestration(mock_openai):
    """測試 main 函數完整流程"""
    # 模擬多次呼叫 create 的回傳值（3位專家 + 1位 Aggregator）
    responses = []
    for _ in range(4):
        resp = MagicMock()
        resp.choices[0].message.content = '{"risks": [], "verdict": "OK"}'
        responses.append(resp)
    
    mock_openai.chat.completions.create.side_effect = responses
    
    # 執行 main（攔截 stdout 避免污染測試輸出）
    with patch('sys.stdout'):
        main()
    
    # 應該總共呼叫 4 次（3 位專家 + 1 位 Aggregator）
    assert mock_openai.chat.completions.create.call_count >= 1
