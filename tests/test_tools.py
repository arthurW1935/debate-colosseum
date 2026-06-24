import pytest
from src.tools.financial_calc import (
    calculate_roi,
    calculate_npv,
    calculate_irr,
    calculate_breakeven,
    financial_calculator
)

def test_calculate_roi():
    assert calculate_roi(1000, 200) == 20.0
    assert calculate_roi(0, 200) == 0.0

def test_calculate_npv():
    cash_flows = [-1000, 500, 500, 500]
    rate = 0.1
    npv = calculate_npv(rate, cash_flows)
    assert round(npv, 2) == 243.43

def test_calculate_irr():
    cash_flows = [-1000, 500, 500, 500]
    irr = calculate_irr(cash_flows)
    assert round(irr, 4) == 0.2338

def test_calculate_breakeven():
    assert calculate_breakeven(1000, 50, 30) == 50.0
    assert calculate_breakeven(1000, 20, 30) == float('inf')

def test_financial_calculator_tool():
    res = financial_calculator.invoke({
        "principal": 1000,
        "rate": 0.1,
        "periods": 3,
        "cash_flows": [-1000, 500, 500, 500],
        "net_profit": 200,
        "fixed_costs": 1000,
        "price_per_unit": 50,
        "variable_cost_per_unit": 30
    })
    assert res["roi_percentage"] == 20.0
    assert round(res["npv"], 2) == 243.43
    assert round(res["irr_decimal"], 4) == 0.2338
    assert res["breakeven_units"] == 50.0
import pytest
from unittest.mock import patch, MagicMock
from src.tools.web_search import web_search

@patch("src.tools.web_search.requests.post")
def test_web_search_success(mock_post):
    # Mocking successful search response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"title": "Search Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
            {"title": "Search Result 2", "url": "https://example.com/2", "content": "Snippet 2"},
        ]
    }
    mock_post.return_value = mock_response
    
    with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        results = web_search("query text")
        
    assert len(results) == 2
    assert results[0] == {
        "title": "Search Result 1",
        "url": "https://example.com/1",
        "snippet": "Snippet 1"
    }
    assert results[1] == {
        "title": "Search Result 2",
        "url": "https://example.com/2",
        "snippet": "Snippet 2"
    }

@patch("src.tools.web_search.requests.post")
def test_web_search_retry_on_429(mock_post):
    # Mock 429 rate limit error on first call, success on second call
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {
        "results": [
            {"title": "Search Result 1", "url": "https://example.com/1", "content": "Snippet 1"}
        ]
    }
    
    mock_post.side_effect = [mock_response_429, mock_response_200]
    
    with patch("time.sleep") as mock_sleep, patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        results = web_search("query text")
        mock_sleep.assert_called_once_with(2)
        
    assert len(results) == 1
    assert results[0]["title"] == "Search Result 1"

@patch("src.tools.web_search.requests.post")
def test_web_search_raises_after_retry(mock_post):
    # Mock rate limit on both attempts
    import requests
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError("Rate Limit Exceeded")
    
    mock_post.side_effect = [mock_response_429, mock_response_429]
    
    with patch("time.sleep"), patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
        with pytest.raises(RuntimeError, match="web_search failed"):
            web_search("query text")

def test_web_search_no_api_key():
    with patch.dict("os.environ", {"TAVILY_API_KEY": ""}, clear=True):
        with pytest.raises(ValueError, match="TAVILY_API_KEY environment variable is not set"):
            web_search("query text")
