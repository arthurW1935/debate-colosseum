import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from src.config import settings
from src.auth.google_oauth import get_google_auth_url, exchange_code_for_tokens, get_google_user_info
from src.auth.jwt_handler import create_access_token
from src.auth.dependencies import get_current_user
from src.db.user_store import upsert_user

auth_router = APIRouter()

@auth_router.get("/google/login")
async def google_login():
    """Returns the Google OAuth login URL for the frontend to redirect to"""
    redirect_uri = f"{settings.API_BASE_URL}/auth/google/callback"
    url = get_google_auth_url(redirect_uri)
    return {"auth_url": url}

@auth_router.get("/google/callback")
async def google_callback(code: str, request: Request):
    """Handles the OAuth callback from Google"""
    from src.auth.session_manager import get_session_manager
    redirect_uri = f"{settings.API_BASE_URL}/auth/google/callback"
    try:
        tokens = await exchange_code_for_tokens(code, redirect_uri)
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from Google")
            
        user_info = await get_google_user_info(access_token)
        
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", "Unknown User")
        avatar_url = user_info.get("picture")
        
        # Upsert user into database
        db_user = upsert_user(email=email, name=name, avatar_url=avatar_url, google_id=google_id)
        
        # Use internal DB ID for JWT payload
        jwt_token = create_access_token(user_id=str(db_user.id), email=email, name=name)
        
        # Create session
        manager = get_session_manager()
        manager.create_session(str(db_user.id), jwt_token, request)
        
        # Redirect to frontend callback page with the token
        frontend_callback = f"{settings.FRONTEND_URL}/auth/callback?token={urllib.parse.quote(jwt_token)}"
        return RedirectResponse(url=frontend_callback)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@auth_router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Returns current user info (requires auth)"""
    return user
