import pytest
import time
from fastapi.testclient import TestClient

from src.api.main import app
from src.middleware.rate_limiter import general_limiter, run_creation_limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_limiters():
    general_limiter.history.clear()
    run_creation_limiter.history.clear()
    yield

def test_requests_within_limit_pass():
    for _ in range(15):
        response = client.get("/runs/non-existent/status")
        assert response.status_code == 404
        assert "X-RateLimit-Remaining" in response.headers

def test_requests_exceeding_limit_return_429():
    for _ in range(15):
        client.get("/runs/non-existent/status")
    
    response = client.get("/runs/non-existent/status")
    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
    assert "Retry-After" in response.headers

def test_window_slides_correctly(monkeypatch):
    current_time = 1000.0
    
    def mock_time():
        return current_time
        
    monkeypatch.setattr(time, "time", mock_time)
    
    for _ in range(15):
        client.get("/runs/non-existent/status")
        
    response = client.get("/runs/non-existent/status")
    assert response.status_code == 429
    
    current_time += 61.0
    
    response = client.get("/runs/non-existent/status")
    assert response.status_code == 404

def test_run_creation_has_separate_stricter_limit():
    for _ in range(5):
        response = client.post("/runs", data={"problem_statement": "test rate limit run"})
        assert response.status_code == 202
        
    response = client.post("/runs", data={"problem_statement": "test rate limit run"})
    assert response.status_code == 429
    assert response.json()["window"] == "1 hour"
    assert "X-RateLimit-Remaining" in response.headers
    
    response = client.get("/runs/non-existent/status")
    assert response.status_code == 404

def test_different_users_have_independent_limits():
    user1_token = "header.eyJ1c2VyX2lkIjogIjEifQ.signature"
    user2_token = "header.eyJ1c2VyX2lkIjogIjIifQ.signature"

    for _ in range(15):
        client.get("/runs/non-existent/status", headers={"Authorization": f"Bearer {user1_token}"})
        
    response1 = client.get("/runs/non-existent/status", headers={"Authorization": f"Bearer {user1_token}"})
    assert response1.status_code == 429
    
    response2 = client.get("/runs/non-existent/status", headers={"Authorization": f"Bearer {user2_token}"})
    assert response2.status_code == 404
