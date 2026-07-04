"""FastAPI backend for Debate Colosseum.

Endpoints
---------
POST  /runs                    D1 — start a new debate run
GET   /runs/{run_id}/status    D1 — poll run state
POST  /runs/{run_id}/review    D3 — submit HITL decision (approve/feedback/abandon)

The LangGraph graph is imported lazily so this file is usable during Phase 1
even while src/graph.py is still empty.  Each run executes the graph in a
background asyncio task; the run record held in _runs tracks status and state.
"""

import asyncio
import io
import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Literal, Optional

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.middleware.rate_limiter import RateLimitMiddleware

from src.config import settings
from src.hitl.review import handle_review
from src.schemas import DecisionMemo, GraphState

logger = logging.getLogger(__name__)

from src.db.run_store import create_run as store_create_run, get_run, update_run, list_user_runs, RunRecord

_checkpointer = None  # initialised in lifespan


# ---------------------------------------------------------------------------
# App lifespan — initialise checkpointer once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _checkpointer
    # D2: Use MemorySaver for Phase 1 MVP.
    # Swap to SqliteSaver ("debate_colosseum.db") when persistence is needed.
    from langgraph.checkpoint.memory import MemorySaver

    _checkpointer = MemorySaver()
    logger.info("LangGraph checkpointer initialised (MemorySaver)")

    async def cleanup_loop():
        manager = get_session_manager()
        while True:
            try:
                await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL_MINUTES * 60)
                count = await asyncio.to_thread(manager.cleanup_expired)
                if count > 0:
                    logger.info("Cleaned up %d expired sessions", count)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in session cleanup task: %s", exc)

    cleanup_task = asyncio.create_task(cleanup_loop())

    yield
    cleanup_task.cancel()
    logger.info("Shutting down — checkpointer released")


app = FastAPI(title="Debate Colosseum API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
from src.auth.router import auth_router
from src.auth.dependencies import get_current_user
from src.auth.session_router import session_router
from src.auth.session_manager import get_session_manager
from fastapi import Request
import asyncio

app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def session_middleware(request: Request, call_next):
    return await call_next(request)

@app.middleware("http")
async def session_refresh_middleware(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        manager = get_session_manager()
        try:
            await asyncio.to_thread(manager.refresh_session, token)
        except Exception as exc:
            logger.warning("Failed to refresh session: %s", exc)
            
    response = await call_next(request)
    return response

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(session_router, prefix="/api/sessions", tags=["sessions"])

# ---------------------------------------------------------------------------
# Background graph runner
# ---------------------------------------------------------------------------

async def _run_graph(run_id: str, state: GraphState) -> None:
    """Execute the LangGraph graph for a run, handling interrupt pauses."""
    record = get_run(run_id)
    if not record:
        return
    try:
        # Lazy import — graph.py is wired in Phase 3 (task I1).
        from src.graph import build_graph  # type: ignore[import]

        graph = build_graph(_checkpointer)
        config = {"configurable": {"thread_id": run_id}}

        result = await asyncio.wait_for(
            asyncio.to_thread(
                graph.invoke,
                state.model_dump(mode="json"),
                config,
            ),
            timeout=600,  # 10-minute hard limit — ~25 LLM calls expected
        )

        # Check if the graph has paused at the interrupt point.
        state_snapshot = graph.get_state(config)
        
        if isinstance(result, dict):
            state_fields = {k: v for k, v in result.items() if not k.startswith("__")}
            record.state = GraphState.model_validate(state_fields)

        if "human_review" in state_snapshot.next:
            record.status = "awaiting_review"
            logger.info("Run %s paused at human_review interrupt", run_id)
        else:
            record.status = "completed"
            logger.info("Run %s completed", run_id)

    except ImportError:
        logger.warning(
            "src/graph.py not yet implemented (Phase 3) — run_id=%s queued but idle",
            run_id,
        )
        record.status = "error"
        record.error = "Graph not yet implemented (see Phase 3, task I1)"
    except asyncio.TimeoutError:
        logger.error("Graph execution timed out after 10 minutes for run_id=%s", run_id)
        record.status = "error"
        record.error = "Graph execution timed out (>10 min). Check API keys and network connectivity."
    except Exception as exc:
        logger.exception("Graph execution failed for run_id=%s", run_id)
        record.status = "error"
        record.error = str(exc)
    finally:
        update_run(run_id, record.status, record.state, record.error)


async def _resume_graph(run_id: str) -> None:
    """Resume a graph that was paused at an interrupt (used after HITL feedback)."""
    record = get_run(run_id)
    if not record:
        return
    try:
        from langgraph.types import Command  # type: ignore[import]
        from src.graph import build_graph  # type: ignore[import]

        graph = build_graph(_checkpointer)
        config = {"configurable": {"thread_id": run_id}}

        # Write the updated state to the checkpointer explicitly
        await asyncio.to_thread(
            graph.update_state,
            config,
            record.state.model_dump(mode="json"),
        )
        
        # Resume graph execution
        result = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, None, config),
            timeout=600,
        )

        state_snapshot = graph.get_state(config)
        
        if isinstance(result, dict):
            state_fields = {k: v for k, v in result.items() if not k.startswith("__")}
            record.state = GraphState.model_validate(state_fields)

        if "human_review" in state_snapshot.next:
            record.status = "awaiting_review"
            logger.info("Run %s re-paused at human_review after feedback", run_id)
        else:
            record.status = "completed"
            logger.info("Run %s completed after feedback loop", run_id)

    except ImportError:
        record.status = "error"
        record.error = "Graph not yet implemented (see Phase 3, task I1)"
    except Exception as exc:
        logger.exception("Graph resume failed for run_id=%s", run_id)
        record.status = "error"
        record.error = str(exc)
    finally:
        update_run(run_id, record.status, record.state, record.error)


# ---------------------------------------------------------------------------
# D4 — External action (Slack webhook)
# ---------------------------------------------------------------------------

def _format_memo_for_slack(memo: DecisionMemo) -> str:
    disagreements = "\n".join(f"• {d}" for d in memo.key_disagreements) or "None"
    next_steps = "\n".join(f"• {s}" for s in memo.next_steps)
    arbitration = f"\n*Arbitration:* {memo.arbitration_summary}" if memo.arbitration_summary else ""
    return (
        f"*Debate Colosseum — Decision Memo*\n"
        f"*Recommendation:* {memo.recommendation.value.upper()} "
        f"(confidence {memo.confidence:.0%}){arbitration}\n\n"
        f"*Executive Summary*\n{memo.executive_summary}\n\n"
        f"*Key Disagreements*\n{disagreements}\n\n"
        f"*Next Steps*\n{next_steps}\n\n"
        f"_Generated {memo.generated_at}_"
    )


async def _execute_action(run_id: str) -> None:
    """D4: POST the decision memo to the configured Slack webhook."""
    record = get_run(run_id)
    if not record:
        return
    webhook_url = settings.SLACK_WEBHOOK_URL

    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not configured — skipping external action")
        record.state = record.state.model_copy(
            update={"action_status": "skipped: SLACK_WEBHOOK_URL not set"}
        )
        record.status = "completed"
        update_run(run_id, record.status, record.state, record.error)
        return

    memo = record.state.final_memo
    if not memo:
        record.state = record.state.model_copy(
            update={"action_status": "error: no memo available to send"}
        )
        record.status = "completed"
        update_run(run_id, record.status, record.state, record.error)
        return

    try:
        message = _format_memo_for_slack(memo)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json={"text": message})
            resp.raise_for_status()
        record.state = record.state.model_copy(update={"action_status": "sent"})
        record.status = "completed"
        logger.info("Slack memo sent for run_id=%s", run_id)
    except Exception as exc:
        logger.exception("Slack action failed for run_id=%s", run_id)
        record.state = record.state.model_copy(
            update={"action_status": f"error: {exc}"}
        )
        record.status = "completed"
    finally:
        update_run(run_id, record.status, record.state, record.error)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_pdf_text(content: bytes) -> str:
    """Extract plain text from PDF bytes.  Returns empty string on failure."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        logger.warning("PDF text extraction failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class RunCreateResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    current_turn: int
    feedback_round: int
    guardrail_passed: bool
    final_memo: Optional[dict] = None
    action_status: Optional[str] = None
    error: Optional[str] = None


class ReviewRequest(BaseModel):
    decision: Literal["approved", "feedback", "abandoned"]
    feedback_text: Optional[str] = None
    edited_memo: Optional[dict] = None


class ReviewResponse(BaseModel):
    run_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/runs", response_model=RunCreateResponse, status_code=202)
async def create_run(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    problem_statement: str = Form(...),
    files: Optional[list[UploadFile]] = File(default=None),
) -> RunCreateResponse:
    """D1: Start a new debate run.

    Accepts a problem statement and optional context files (PDF / txt / md).
    Returns a run_id immediately; the graph executes in the background.
    Poll GET /runs/{run_id}/status for progress.
    """
    # D2: generate a stable run_id for checkpointer threading
    run_id = str(uuid.uuid4())

    context_docs: list[str] = []
    for upload in files or []:
        # Skip empty-string placeholders that Swagger sends when no file is chosen
        if not upload.filename:
            continue
        raw = await upload.read()
        filename = upload.filename.lower()
        if filename.endswith(".pdf"):
            text = _extract_pdf_text(raw)
        else:
            text = raw.decode("utf-8", errors="replace")
        if text.strip():
            context_docs.append(text)

    state = GraphState(
        problem_statement=problem_statement,
        context_docs=context_docs,
        run_id=run_id,
    )

    # Use a dummy user_id for now until auth is integrated
    user_id = "temp_user"
    store_create_run(run_id, user_id, problem_statement, context_docs, state)
    record = get_run(run_id)

    task = asyncio.create_task(_run_graph(run_id, state))
    if record:
        record._task = task

    logger.info("Run created: run_id=%s docs=%d", run_id, len(context_docs))
    return RunCreateResponse(run_id=run_id, status="running")


@app.get("/runs/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str, user: dict = Depends(get_current_user)) -> RunStatusResponse:
    """D1: Poll current run state.

    status values:
      running         — graph is executing
      awaiting_review — graph paused at human_review interrupt
      completed       — run finished (approved + action sent, or abandoned)
      error           — unhandled exception; see `error` field
    """
    record = get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    memo_dict = record.state.final_memo.model_dump(mode="json") if record.state.final_memo else None

    return RunStatusResponse(
        run_id=run_id,
        status=record.status,
        current_turn=record.state.current_turn,
        feedback_round=record.state.feedback_round,
        guardrail_passed=record.state.guardrail_passed,
        final_memo=memo_dict,
        action_status=record.state.action_status,
        error=record.error,
    )


@app.post("/runs/{run_id}/review", response_model=ReviewResponse)
async def review_run(
    run_id: str,
    body: ReviewRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
) -> ReviewResponse:
    """D3: Submit a human review decision.

    Allowed decisions:
      approved  — triggers the external Slack action; run ends
      feedback  — feedback_text required; graph re-enters processing
      abandoned — saves state, no external action; run ends
    """
    record = get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    if record.status != "awaiting_review":
        raise HTTPException(
            status_code=409,
            detail=f"Run is not awaiting review (current status: {record.status})",
        )

    # Apply decision to state (pure function — no side effects)
    record.state = handle_review(
        record.state,
        decision=body.decision,
        feedback_text=body.feedback_text,
        edited_memo=body.edited_memo,
    )

    if body.decision == "abandoned":
        record.status = "completed"
        update_run(run_id, record.status, record.state, record.error)
        return ReviewResponse(
            run_id=run_id,
            status="completed",
            message="Run abandoned — state saved, no external action taken.",
        )

    if body.decision == "approved":
        record.status = "running"
        update_run(run_id, record.status, record.state, record.error)
        task = asyncio.create_task(_execute_action(run_id))
        record._task = task
        return ReviewResponse(
            run_id=run_id,
            status="running",
            message="Approved — sending memo to Slack.",
        )

    # feedback: resume graph with updated state
    record.status = "running"
    update_run(run_id, record.status, record.state, record.error)
    task = asyncio.create_task(_resume_graph(run_id))
    record._task = task
    return ReviewResponse(
        run_id=run_id,
        status="running",
        message=f"Feedback submitted (round {record.state.feedback_round}) — re-processing.",
    )

@app.get("/runs")
async def list_runs(user_id: Optional[str] = None):
    # Wait for Auth branch to provide user_id properly, for now use optional query param
    uid = user_id or "temp_user"
    runs = list_user_runs(uid)
    return {"runs": runs}

