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
