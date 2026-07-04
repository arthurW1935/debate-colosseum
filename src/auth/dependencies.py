from fastapi import Header, HTTPException
from typing import Optional
from src.auth.jwt_handler import decode_access_token

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        return {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name")
        }
    except HTTPException:
        return None

def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name")
    }
