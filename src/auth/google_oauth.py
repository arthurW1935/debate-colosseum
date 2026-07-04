import urllib.parse
import httpx
from fastapi import HTTPException
from src.config import settings
import logging

logger = logging.getLogger(__name__)

GOOGLE_OAUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def get_google_auth_url(redirect_uri: str) -> str:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google Client ID not configured")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_OAUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    with httpx.Client() as client:
        response = client.post(GOOGLE_TOKEN_URL, data=data)
        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange auth code")
        return response.json()

def get_google_user_info(access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    with httpx.Client() as client:
        response = client.get(GOOGLE_USERINFO_URL, headers=headers)
        if response.status_code != 200:
            logger.error(f"Google userinfo failed: {response.text}")
            raise HTTPException(status_code=400, detail="Failed to fetch user info")
        return response.json()
