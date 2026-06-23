# Activity Trace Log

This file maintains a running log of all actions taken by the AI orchestrator and its subagents.

## Completed Actions

- **Project Scaffold Verification:** Verified that the user successfully created the directory structures for `src`, `tests`, and `frontend`.
- **.gitignore Update:** Created a comprehensive `.gitignore` file for Python environments, API keys, and LangSmith metadata.
- **Phase 0 Execution (Schemas, Config, Fixtures):**
  - Subagent generated Pydantic v2 schemas in `src/schemas.py`.
  - Subagent generated LangChain agnostic config in `src/config.py` (supporting Anthropic, OpenAI, and Vertex AI via `pydantic-settings`).
  - Subagent created mock JSON files in `tests/fixtures/`.
- **Phase 1 Trial & Reversion:** Launched subagents for Phase 1 (Tracks A, B, C, D) but reverted all their changes via `git restore` per user instructions to maintain explicit permission controls.
- **Manual Git Commits & Fixes:** The user manually committed the Phase 0 files (`src/schemas.py`, `src/config.py`, fixtures, etc.), created `.env.example`, and later manually fixed `.env.example` to include the missing `LANGSMITH_ENDPOINT` configuration.
- **Config & Documentation Update:** Orchestrator added `LANGSMITH_ENDPOINT` handling to `src/config.py` and appended a Mermaid UML schema diagram to the end of `PLAN.md`.
- **Config Alignment:** Orchestrator updated `src/config.py` to natively map all `LANGSMITH_*` variables exactly as they were defined by the user in `.env.example` to the standard `LANGCHAIN_*` OS variables, and explicitly stripped out the unused `LANGCHAIN_` configuration aliases from the Pydantic schema to strictly match the `.env.example` file.

---

## Phase 1 — Track D Implementation (App, HITL, Eval)

**Owner: Person D (this session)**  
**Date: 2026-06-23**

### D9 — LangSmith tracing infrastructure (`src/config.py`)
- Added `TAVILY_API_KEY` and `SLACK_WEBHOOK_URL` to `Settings` to match `.env.example` requirements from INSTRUCTIONS.md.
- Changed default `LLM_PROVIDER` from `"openai"` to `"anthropic"` and `LLM_MODEL` to `"claude-sonnet-4-6"` per PRD TRD §18 (tech stack: Claude claude-sonnet-4-6 via Anthropic API).
- Renamed `LANGSMITH_PROJECT` default from `debate_colosseum` → `debate-colosseum` to match INSTRUCTIONS.md.
- Cleaned up docstring and logging imports.

### D3 — HITL review logic (`src/hitl/review.py`)
- Implemented `handle_review(state, decision, feedback_text, edited_memo) → GraphState`.
- Pure function — no side effects; state is deep-copied before mutation so callers get a new object.
- On `"feedback"`: increments `feedback_round`, sets `current_feedback_text`, appends a `HumanFeedbackEntry` to `human_feedback_history`.
- On `"approved"`: applies any `edited_memo` overrides to `final_memo` before the Slack action fires.
- On `"abandoned"`: patches the last `HumanFeedbackEntry.resolved_by` to `"abandoned"`.
- Designed for independent testing without a running graph.

### D1 + D2 + D3 + D4 — FastAPI backend (`src/api/main.py`)
- **D1** `POST /runs`: accepts `problem_statement` (form field) + optional file uploads (PDF/txt/md). Extracts PDF text via PyPDF2. Creates a `GraphState`, stores a `RunRecord`, fires `_run_graph` as an asyncio background task. Returns `{run_id, status}` with HTTP 202.
- **D1** `GET /runs/{run_id}/status`: returns `{run_id, status, current_turn, feedback_round, guardrail_passed, final_memo, action_status, error}`. Status values: `running | awaiting_review | completed | error`.
- **D2** Run IDs are UUIDs generated at `POST /runs`. `MemorySaver` (LangGraph) is initialised at app lifespan startup. Comment notes the swap path to `SqliteSaver` for persistence.
- **D3** `POST /runs/{run_id}/review`: enforces `status == "awaiting_review"` precondition (409 otherwise). Delegates state mutation to `handle_review`. Routes: `approved` → `_execute_action` background task; `feedback` → `_resume_graph` background task; `abandoned` → sets status `completed` immediately.
- `_run_graph`: lazy-imports `src.graph.build_graph` so Phase 1 runs without a wired graph. Detects LangGraph interrupt by checking `"__interrupt__"` key in result dict; sets `status = "awaiting_review"` when found. Graceful `ImportError` path returns `error` status with a Phase 3 note.
- `_resume_graph`: uses `langgraph.types.Command(resume=...)` pattern to resume from interrupt checkpoint.
- **D4** `_execute_action`: POSTs the formatted `DecisionMemo` to `SLACK_WEBHOOK_URL` via `httpx.AsyncClient`. Handles missing webhook, missing memo, and HTTP errors without crashing the process. Writes result to `state.action_status`.
- `_format_memo_for_slack`: produces a Slack-formatted string with recommendation, summary, disagreements, next steps.
- CORS middleware added for Streamlit ↔ FastAPI communication.

### D5 + D6 + D7 + D8 — Streamlit frontend (`frontend/app.py`)
- **D5** Problem input page: `st.text_area` for problem statement, `st.file_uploader` (PDF/txt/md, multi-file) with file preview. Form submission calls `POST /runs` and stores `run_id` in `st.session_state`.
- **D6** Debate timeline: rendered from `GET /status` response. Shows 8 phase rows (ingestion → review) with ✅/⏳/⬜ icons derived from `current_turn`, `guardrail_passed`, `status`, and `has_memo`. Feedback loop round shown separately. Auto-polls every 2 seconds via `time.sleep` + `st.rerun()` while `status == "running"`.
- **D7** Memo review: `render_memo()` renders executive summary, recommendation badge, key agreements/disagreements columns, arbitration summary, next steps, risk register table (with severity colour icons), and expert positions tabs. Confidence and feedback revision count shown inline.
- **D8** HITL controls: three-column layout (Approve / Send Feedback / Abandon). Feedback action toggles an inline `st.form` for free-text input; submit calls `POST /runs/{id}/review` with `decision="feedback"`. Approve calls with `decision="approved"`. Abandon calls with `decision="abandoned"`. All actions set `st.session_state["status"]` and `st.rerun()`.
- Sidebar shows run metadata (run_id, status, turn, feedback rounds) and "← New debate" reset button.

### D10 — Eval harness (`tests/eval/run_eval.py`)
- 5 hardcoded eval scenarios matching PRD §16:
  1. EU expansion — full debate path with RAG financial doc
  2. Discount campaign — consensus early exit (no Turn 2 expected)
  3. Competitor acquisition — arbiter trigger scenario
  4. Early hiring with burn rate doc — RAG meaningfully affects outputs
  5. Prompt injection — guardrail block expected
- Each scenario records: run_id, routing path (node sequence), disagreement scores (t1/t2), `guardrail_passed`, final memo.
- `_run_graph` calls `src.graph.build_graph()` directly (no FastAPI); `MemorySaver` used for checkpointing.
- Graceful `ImportError` when graph is not yet implemented (Phase 1 state) — logs warning, continues.
- Results saved to `logs/eval_results/scenario_<id>_<timestamp>.json`.
- CLI: `--scenario all|1|2|3|4|5`.

### Infrastructure
- Created `tests/__init__.py`, `tests/eval/__init__.py`, `logs/eval_results/` directory.

---

## Current State

- Codebase is at **Phase 1 complete (Track D)**.
- Track D is fully implemented and wire-ready for Phase 3 graph assembly.
- Awaiting Tracks A, B, C to complete Phase 1 before Phase 2 (cross-track wiring) can begin.
- `src/graph.py` is empty — eval harness and HITL resume will fail gracefully with ImportError until Phase 3 (task I1).

## Known Issues / Flags for Other Tracks

- `src/guardrails.py/checks.py` — directory is named `guardrails.py` (with `.py` suffix) instead of `guardrails/`. Track C should rename this before implementing checks.py to avoid import errors.
- `src/agents/synthesiser.py` — British spelling vs `synthesizer` used everywhere else. Track C should rename before implementing.
