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
- Codebase is at **Track A (RAG Pipeline & Shared Tools)** completion.
- Awaiting next track inputs or other integration tasks.
