from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserDB(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    created_at: datetime

class RunDB(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    problem_statement: str
    status: str
    state_json: str
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
