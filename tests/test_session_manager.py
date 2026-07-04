import pytest
import datetime
import uuid
from unittest.mock import Mock, patch
from src.auth.session_manager import InMemorySessionManager, hash_token, get_session_manager
from fastapi import Request

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "test-agent"}
    return request

def test_in_memory_creation_stores_hashed_token(mock_request):
    manager = InMemorySessionManager()
    user_id = str(uuid.uuid4())
    token = "secret-token"
    
    session_id = manager.create_session(user_id, token, mock_request)
    assert session_id in manager.sessions
    
    session = manager.sessions[session_id]
    assert session["token_hash"] == hash_token(token)
    assert session["user_id"] == user_id
    assert session["ip_address"] == "127.0.0.1"

def test_session_validation_works(mock_request):
    manager = InMemorySessionManager()
    token = "secret-token"
    manager.create_session("user-1", token, mock_request)
    
    session = manager.validate_session(token)
    assert session is not None
    assert session["user_id"] == "user-1"
    
def test_expired_sessions_are_rejected(mock_request):
    manager = InMemorySessionManager()
    token = "secret-token"
    session_id = manager.create_session("user-1", token, mock_request)
    
    # manually expire it
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    manager.sessions[session_id]["expires_at"] = past.isoformat()
    
    session = manager.validate_session(token)
    assert session is None

def test_session_revocation(mock_request):
    manager = InMemorySessionManager()
    token = "secret-token"
    session_id = manager.create_session("user-1", token, mock_request)
    
    manager.revoke_session(session_id, "user-1")
    assert manager.validate_session(token) is None
    
def test_cleanup_removes_expired(mock_request):
    manager = InMemorySessionManager()
    # 1 valid, 2 expired
    manager.create_session("user-1", "token-1", mock_request)
    
    s2 = manager.create_session("user-2", "token-2", mock_request)
    s3 = manager.create_session("user-3", "token-3", mock_request)
    
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    manager.sessions[s2]["expires_at"] = past.isoformat()
    manager.sessions[s3]["expires_at"] = past.isoformat()
    
    count = manager.cleanup_expired()
    assert count == 2
    assert len(manager.sessions) == 1
    
def test_fallback_works():
    with patch("src.auth.session_manager.settings") as mock_settings:
        mock_settings.SUPABASE_URL = None
        mock_settings.SUPABASE_KEY = None
        import src.auth.session_manager as sm
        sm._session_manager_instance = None
        manager = sm.get_session_manager()
        assert isinstance(manager, sm.InMemorySessionManager)
