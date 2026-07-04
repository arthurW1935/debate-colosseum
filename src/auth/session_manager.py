import datetime
import hashlib
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from fastapi import Request
from src.config import settings

logger = logging.getLogger(__name__)

def hash_token(token: str) -> str:
    """Hashes a token using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

class BaseSessionManager(ABC):
    @abstractmethod
    def create_session(self, user_id: str, token: str, request: Request, session_id: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def validate_session(self, token: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def refresh_session(self, token: str):
        pass

    @abstractmethod
    def revoke_session(self, session_id: str, user_id: str):
        pass

    @abstractmethod
    def revoke_all_sessions(self, user_id: str):
        pass

    @abstractmethod
    def list_sessions(self, user_id: str) -> List[Dict]:
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        pass

class SupabaseSessionManager(BaseSessionManager):
    def __init__(self, client):
        self.supabase = client

    def create_session(self, user_id: str, token: str, request: Request, session_id: Optional[str] = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        token_hash = hash_token(token)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(hours=settings.SESSION_TTL_HOURS)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        data = {
            "id": session_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "created_at": now.isoformat(),
            "last_active_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        
        self.supabase.table("sessions").insert(data).execute()
        return session_id

    def validate_session(self, token: str) -> Optional[Dict]:
        token_hash = hash_token(token)
        response = self.supabase.table("sessions").select("*").eq("token_hash", token_hash).execute()
        if not response.data:
            return None
        
        session = response.data[0]
        expires_at = datetime.datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
        
        if datetime.datetime.now(datetime.timezone.utc) > expires_at:
            return None
            
        return session

    def refresh_session(self, token: str):
        token_hash = hash_token(token)
        now = datetime.datetime.now(datetime.timezone.utc)
        self.supabase.table("sessions").update({"last_active_at": now.isoformat()}).eq("token_hash", token_hash).execute()

    def revoke_session(self, session_id: str, user_id: str):
        self.supabase.table("sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()

    def revoke_all_sessions(self, user_id: str):
        self.supabase.table("sessions").delete().eq("user_id", user_id).execute()

    def list_sessions(self, user_id: str) -> List[Dict]:
        response = self.supabase.table("sessions").select("id, created_at, last_active_at, ip_address, user_agent").eq("user_id", user_id).execute()
        return response.data

    def cleanup_expired(self) -> int:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        response = self.supabase.table("sessions").delete().lt("expires_at", now).execute()
        return len(response.data) if response.data else 0

class InMemorySessionManager(BaseSessionManager):
    def __init__(self):
        # session_id -> dict
        self.sessions = {}
        # token_hash -> session_id
        self.tokens = {}

    def create_session(self, user_id: str, token: str, request: Request, session_id: Optional[str] = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        token_hash = hash_token(token)
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(hours=settings.SESSION_TTL_HOURS)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        session_data = {
            "id": session_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "created_at": now.isoformat(),
            "last_active_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        
        self.sessions[session_id] = session_data
        self.tokens[token_hash] = session_id
        return session_id

    def validate_session(self, token: str) -> Optional[Dict]:
        token_hash = hash_token(token)
        session_id = self.tokens.get(token_hash)
        if not session_id:
            return None
            
        session = self.sessions.get(session_id)
        if not session:
            return None
            
        expires_at = datetime.datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
        if datetime.datetime.now(datetime.timezone.utc) > expires_at:
            return None
            
        return session

    def refresh_session(self, token: str):
        token_hash = hash_token(token)
        session_id = self.tokens.get(token_hash)
        if session_id and session_id in self.sessions:
            now = datetime.datetime.now(datetime.timezone.utc)
            self.sessions[session_id]["last_active_at"] = now.isoformat()

    def revoke_session(self, session_id: str, user_id: str):
        session = self.sessions.get(session_id)
        if session and session["user_id"] == user_id:
            token_hash = session["token_hash"]
            del self.sessions[session_id]
            if token_hash in self.tokens:
                del self.tokens[token_hash]

    def revoke_all_sessions(self, user_id: str):
        to_delete = [sid for sid, s in self.sessions.items() if s["user_id"] == user_id]
        for sid in to_delete:
            token_hash = self.sessions[sid]["token_hash"]
            del self.sessions[sid]
            if token_hash in self.tokens:
                del self.tokens[token_hash]

    def list_sessions(self, user_id: str) -> List[Dict]:
        result = []
        for s in self.sessions.values():
            if s["user_id"] == user_id:
                result.append({
                    "id": s["id"],
                    "created_at": s["created_at"],
                    "last_active_at": s["last_active_at"],
                    "ip_address": s["ip_address"],
                    "user_agent": s["user_agent"]
                })
        return result

    def cleanup_expired(self) -> int:
        now = datetime.datetime.now(datetime.timezone.utc)
        to_delete = []
        for sid, s in self.sessions.items():
            expires_at = datetime.datetime.fromisoformat(s["expires_at"].replace("Z", "+00:00"))
            if now > expires_at:
                to_delete.append(sid)
                
        for sid in to_delete:
            token_hash = self.sessions[sid]["token_hash"]
            del self.sessions[sid]
            if token_hash in self.tokens:
                del self.tokens[token_hash]
                
        return len(to_delete)

_session_manager_instance = None

def get_session_manager() -> BaseSessionManager:
    global _session_manager_instance
    if _session_manager_instance is not None:
        return _session_manager_instance
        
    # Attempt to initialize Supabase
    supabase_url = getattr(settings, "SUPABASE_URL", None)
    supabase_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None) or getattr(settings, "SUPABASE_ANON_KEY", None)
    
    if supabase_url and supabase_key:
        try:
            from supabase import create_client, Client
            client: Client = create_client(supabase_url, supabase_key)
            _session_manager_instance = SupabaseSessionManager(client)
            logger.info("Initialized SupabaseSessionManager")
        except ImportError:
            logger.warning("supabase package not found. Falling back to InMemorySessionManager.")
            _session_manager_instance = InMemorySessionManager()
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to InMemorySessionManager.")
            _session_manager_instance = InMemorySessionManager()
    else:
        logger.info("Supabase credentials not found. Using InMemorySessionManager.")
        _session_manager_instance = InMemorySessionManager()
        
    return _session_manager_instance
