import asyncio
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timezone
from src.schemas import GraphState
from src.db.supabase_client import get_supabase
from src.db.models import RunDB
from fastapi import HTTPException

@dataclass
class RunRecord:
    state: GraphState
    status: str = "running"
    error: Optional[str] = None
    _task: Optional[asyncio.Task] = field(default=None, repr=False)

def create_run(run_id: str, user_id: str, problem_statement: str, context_docs: list[str], state: GraphState) -> str:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
        
    data = {
        "id": run_id,
        "user_id": user_id,
        "problem_statement": problem_statement,
        "status": "running",
        "state_json": state.model_dump_json(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    supabase.table("runs").insert(data).execute()
    return run_id

def get_run(run_id: str) -> Optional[RunRecord]:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
        
    res = supabase.table("runs").select("*").eq("id", run_id).execute()
    if res.data:
        row = res.data[0]
        state = GraphState.model_validate_json(row["state_json"])
        record = RunRecord(state=state, status=row["status"], error=row["error"])
        return record
    return None

def update_run(run_id: str, status: str, state: GraphState, error: Optional[str] = None):
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
        
    data = {
        "status": status,
        "state_json": state.model_dump_json(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if error is not None:
        data["error"] = error
        
    supabase.table("runs").update(data).eq("id", run_id).execute()

def list_user_runs(user_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not configured (Supabase is missing).")
        
    res = supabase.table("runs").select("id, problem_statement, status, created_at, updated_at").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data
