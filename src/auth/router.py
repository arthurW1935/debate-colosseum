from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from src.auth.google_oauth import get_google_auth_url, exchange_code_for_tokens, get_google_user_info
from src.auth.jwt_handler import create_access_token
from src.auth.dependencies import get_current_user
from src.config import settings

auth_router = APIRouter()

# In-memory user store for MVP
_users = {}

@auth_router.get("/google/login")
def google_login(request: Request):
    # Determine backend URL from request to handle the callback
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/google/callback"
    
    auth_url = get_google_auth_url(redirect_uri)
    return {"auth_url": auth_url}

@auth_router.get("/google/callback")
def google_callback(request: Request, code: str):
    base_url = str(request.base_url).rstrip("/")
    redirect_uri = f"{base_url}/auth/google/callback"

    tokens = exchange_code_for_tokens(code, redirect_uri)
    access_token = tokens.get("access_token")
    if not access_token:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?error=no_access_token")

    user_info = get_google_user_info(access_token)
    
    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    
    # Upsert user in-memory
    _users[google_id] = {
        "id": google_id,
        "email": email,
        "name": name,
    }
    
    jwt_token = create_access_token(google_id, email, name)
    
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}")

@auth_router.get("/me")
def get_me(user: dict = Depends(get_current_user)):
    return user

@auth_router.post("/logout")
def logout():
    return {"message": "Logout successful, please clear the token on client side."}
