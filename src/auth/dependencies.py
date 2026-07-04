from fastapi import Header, HTTPException, status
from typing import Optional
from src.auth.jwt_handler import decode_access_token

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Returns user dict if valid token provided, else None. Does not enforce auth."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    try:
        # Decode and return payload (which has sub, email, name)
        payload = decode_access_token(token)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
    except HTTPException:
        # Invalid token, but since this is optional, we just return None
        return None

def get_current_user(authorization: str = Header(...)) -> dict:
    """Enforces valid auth token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth format")
    
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name")
    }
