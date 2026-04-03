import pytest
from design_decision_engine import normalize, is_valid_output

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
    """測試 is_valid_output 處理型態錯誤（例如把 list 寫成 dict 或 string）"""
    data_wrong_risks = {
        "risks": "這是一個字串，不是陣列",
        "missing": [],
        "improvements": []
    }
    assert is_valid_output(data_wrong_risks) is False

    data_wrong_missing = {
        "risks": [],
        "missing": {"item": "缺少的東西"},
        "improvements": []
    }
    assert is_valid_output(data_wrong_missing) is False

def test_is_valid_output_missing_key():
    """測試 is_valid_output 少 key 也能靠 data.get 預設 [] 通過檢查"""
    # 如果缺了 'risks' 但其他存在，因為 get 會給預設 []，所以也是 True（因為這是 normalize 過的或者是 fallback 補齊的，is_valid_output 主要是看拿到的是不是 list）
    data_missing_key = {
        "missing": [],
        "improvements": []
    }
    assert is_valid_output(data_missing_key) is True
