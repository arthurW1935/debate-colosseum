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
- **Track A RAG & Shared Tools Implementation:**
  - Implemented `.pdf`, `.txt`, and `.md` file text extraction, text chunking (600/80 recursive splitter), Chroma ephemeral in-memory vector store indexing using local `all-MiniLM-L6-v2` embeddings, and the `ingest_context` node function in `src/rag/ingest.py`.
  - Implemented the `doc_retrieval` tool in `src/tools/doc_retrieval.py` with cosine top-8 similarity and local cross-encoder `ms-marco-MiniLM-L-6-v2` reranking to top 4, including graceful fallback on empty documents.
  - Implemented the `web_search` tool in `src/tools/web_search.py` using Tavily API direct REST requests, supporting rate-limiting 429 retries and schema matching (`{title, url, snippet}`).
  - Created unit and node tests in `tests/test_rag.py`, `tests/test_tools.py`, and `tests/test_ingest_node.py` (16 tests passed).
  - Wrote tool integration handoff documentation in `src/tools/README.md`.

## Current State
- Codebase is at **Phase 0** completion.
- **Track B Preparation**: Fixed the LangGraph state dictionary overwrite issue by adding a custom `merge_dict` reducer and `typing.Annotated` to the `GraphState` Pydantic model in `src/schemas.py`.
- **Time:** [2026-06-23T08:34:00Z] (approx)
- **Status:** COMPLETED
- **Files Touched:**
  - `src/tools/financial_calc.py`
  - `src/agents/base_wrapper.py`
  - `tests/test_tools.py`
- **Actions:**
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
- **Track A RAG & Shared Tools Implementation:**
  - Implemented `.pdf`, `.txt`, and `.md` file text extraction, text chunking (600/80 recursive splitter), Chroma ephemeral in-memory vector store indexing using local `all-MiniLM-L6-v2` embeddings, and the `ingest_context` node function in `src/rag/ingest.py`.
  - Implemented the `doc_retrieval` tool in `src/tools/doc_retrieval.py` with cosine top-8 similarity and local cross-encoder `ms-marco-MiniLM-L-6-v2` reranking to top 4, including graceful fallback on empty documents.
  - Implemented the `web_search` tool in `src/tools/web_search.py` using Tavily API direct REST requests, supporting rate-limiting 429 retries and schema matching (`{title, url, snippet}`).
  - Created unit and node tests in `tests/test_rag.py`, `tests/test_tools.py`, and `tests/test_ingest_node.py` (16 tests passed).
  - Wrote tool integration handoff documentation in `src/tools/README.md`.

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
- Codebase is at **Phase 0** completion.
- **Track B Preparation**: Fixed the LangGraph state dictionary overwrite issue by adding a custom `merge_dict` reducer and `typing.Annotated` to the `GraphState` Pydantic model in `src/schemas.py`.
- **Time:** [2026-06-23T08:34:00Z] (approx)
- **Status:** COMPLETED
- **Files Touched:**
  - `src/tools/financial_calc.py`
  - `src/agents/base_wrapper.py`
  - `tests/test_tools.py`
- **Actions:**
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
- **Track C Execution (Judgment Chain):**
  - Renamed the invalid `src/guardrails.py` package folder to `src/guardrails` to resolve import errors.
  - Implemented the Moderator (`src/agents/moderator.py`) with deterministic disagreement scoring and routing thresholds (Turn 1 and Turn 2).
  - Implemented the Arbiter Agent (`src/agents/arbiter.py`) to rule on specific disputed points.
  - Implemented the Synthesizer Agent (`src/agents/synthesiser.py`) to create initial decision memos and process human feedback (synthesizer-only and targeted agent revision paths).
  - Implemented Guardrails (`src/guardrails/checks.py`) with rule-based and LLM-based policy/safety checks.
  - Wrote and verified comprehensive unit tests (`tests/test_moderator.py`, `tests/test_synthesizer.py`, `tests/test_guardrails.py`).

## Current State
- Track C implementation is complete. All 9 unit tests pass successfully.
- Ready to coordinate integration with other tracks.
- Codebase is at **Phase 0** completion.
- **Track B Preparation**: Fixed the LangGraph state dictionary overwrite issue by adding a custom `merge_dict` reducer and `typing.Annotated` to the `GraphState` Pydantic model in `src/schemas.py`.
- **Time:** [2026-06-23T08:34:00Z] (approx)
- **Status:** COMPLETED
- **Files Touched:**
  - `src/tools/financial_calc.py`
  - `src/agents/base_wrapper.py`
  - `tests/test_tools.py`
- **Actions:**
  - Implemented standalone financial calculations (ROI, NPV, IRR, Breakeven).
  - Created test suite and verified standard math outputs.
  - Implemented `call_agent_with_retry` wrapping `with_structured_output` with robust LangSmith tracing and schema retry limits.
- **Verification:** `pytest tests/test_tools.py` passed cleanly.

### Checkpoint 2: Track B Turn 1 Agents
- **Time:** [2026-06-23T09:12:00Z]
- **Status:** COMPLETED
- **Files Touched:**
  - `src/schemas.py` (fixed enum `Literal` config for LLM generation)
  - `tests/fixtures/mock_tools.py`
  - `src/agents/growth.py`
  - `src/agents/finance.py`
  - `src/agents/risk.py`
  - `tests/test_agents_t1.py`
- **Actions:**
  - Implemented expert agents (Growth, Finance, Risk) using the precise system prompts required for Turn 1.
  - Created mock tools for testing isolated agent behavior without depending on Phase 1 setup.
  - Fixed an unparseable schema Literal to fix Vertex AI API crash.
  - Hardened prompts with strict tool sequencing, padded financial `cash_flows` array rules, and strictly formatted dissent notes (`[Peer Role]: [Specific disagreement]`).
- **Verification:** `pytest tests/test_agents_t1.py` passed cleanly.

### Checkpoint 3: Turn 2 Peer Context Injection
- **Time:** [2026-06-23T09:51:00Z]
- **Status:** COMPLETED
- **Files Touched:**
  - `src/agents/base_wrapper.py`
- **Actions:**
  - Injected conditional prompt logic for `turn == 2`.
  - Added extraction of peers' `turn1_analyses` (recommendation, confidence, summary) and injected it into the user prompt.
  - Injected `disagreement_report_t1` (score, summary) into the user prompt if available.
  - Appended strict formatting instruction for `dissent_notes`.
- **Verification:** Logic structurally verified in `base_wrapper.py`; runtime behavioral verification will happen in Checkpoint 4 (Turn 2 Tests).

### Checkpoint 4: Track B Turn 2 Tests
- **Time:** [2026-06-23T10:00:00Z]
- **Status:** COMPLETED
- **Files Touched:**
  - `tests/test_agents_t2.py` (Created)
- **Actions:**
  - Created Turn 2 test suite for expert agents (`growth`, `finance`, `risk`).
  - Constructed a mock `t2_state` containing `turn1_analyses` and a `disagreement_report_t1` to simulate the environment of Turn 2.
  - Asserted that all agents successfully process the injected peer context and return valid `ExpertAnalysis` structures configured for `round="2"`.
- **Verification:** `pytest tests/test_agents_t2.py` passed cleanly (3/3 tests passed).
- Codebase is at **Track A (RAG Pipeline & Shared Tools)** completion.
- Awaiting next track inputs or other integration tasks.
- Phase 2 (Cross-Track Wiring) Completed. Track A dependencies fixed, agents wired to real tools, and E2E tests passing.

- Codebase is at **Phase 1 complete (Track D)**.
- Track D is fully implemented and wire-ready for Phase 3 graph assembly.
- Awaiting Tracks A, B, C to complete Phase 1 before Phase 2 (cross-track wiring) can begin.
- `src/graph.py` is empty — eval harness and HITL resume will fail gracefully with ImportError until Phase 3 (task I1).

## Known Issues / Flags for Other Tracks

- `src/guardrails.py/checks.py` — directory is named `guardrails.py` (with `.py` suffix) instead of `guardrails/`. Track C should rename this before implementing checks.py to avoid import errors.
- `src/agents/synthesiser.py` — British spelling vs `synthesizer` used everywhere else. Track C should rename before implementing.
