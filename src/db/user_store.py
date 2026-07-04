from typing import Optional
from datetime import datetime, timezone
from src.db.supabase_client import get_supabase
from src.db.models import UserDB
from fastapi import HTTPException

def upsert_user(email: str, name: str, avatar_url: Optional[str] = None, google_id: Optional[str] = None) -> UserDB:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")

    data = {
        "email": email,
        "name": name,
        "avatar_url": avatar_url,
        "google_id": google_id
    }
    
    response = supabase.table("users").select("*").eq("email", email).execute()
    if response.data:
        user_id = response.data[0]['id']
        res = supabase.table("users").update(data).eq("id", user_id).execute()
        return UserDB(**res.data[0])
    else:
        res = supabase.table("users").insert(data).execute()
        return UserDB(**res.data[0])

def get_user_by_id(user_id: str) -> Optional[UserDB]:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
    res = supabase.table("users").select("*").eq("id", user_id).execute()
    if res.data:
        return UserDB(**res.data[0])
    return None

def get_user_by_email(email: str) -> Optional[UserDB]:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
    res = supabase.table("users").select("*").eq("email", email).execute()
    if res.data:
        return UserDB(**res.data[0])
    return None
