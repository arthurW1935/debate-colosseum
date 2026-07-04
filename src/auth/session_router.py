from fastapi import APIRouter, Depends, Header, HTTPException, Request
from typing import Optional
from .session_manager import get_session_manager

session_router = APIRouter()

def get_current_user(
    request: Request,
    user_id: Optional[str] = Header(None, alias="X-User-Id"),
    user_id_query: Optional[str] = None
):
    manager = get_session_manager()
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        session = manager.validate_session(token)
        if session:
            # Our session dict should have user_id and id (session_id)
            return {"user_id": session["user_id"], "id": session["id"]}
            
    # Fallback for simulated auth
    uid = user_id or user_id_query or request.query_params.get("user_id")
    if uid:
        return {"user_id": uid, "id": None}
        
    raise HTTPException(status_code=401, detail="Not authenticated")

@session_router.get("/me")
def get_me(user=Depends(get_current_user)):
    return user

@session_router.get("/sessions")
def list_sessions(user=Depends(get_current_user)):
    manager = get_session_manager()
    sessions = manager.list_sessions(user["user_id"])
    
    current_session_id = user.get("id")
    for s in sessions:
        s["is_current"] = (s["id"] == current_session_id)
        
    return sessions

@session_router.delete("/sessions/{session_id}")
def revoke_session(session_id: str, user=Depends(get_current_user)):
    manager = get_session_manager()
    manager.revoke_session(session_id, user["user_id"])
    return {"status": "success"}

@session_router.post("/logout")
def logout(user=Depends(get_current_user)):
    manager = get_session_manager()
    current_session_id = user.get("id")
    if current_session_id:
        manager.revoke_session(current_session_id, user["user_id"])
    return {"status": "success"}

@session_router.post("/logout-all")
def logout_all(user=Depends(get_current_user)):
    manager = get_session_manager()
    manager.revoke_all_sessions(user["user_id"])
    return {"status": "success"}
