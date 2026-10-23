# Debate Colosseum

A multi-agent platform for business decisions. You describe a decision, and a panel of AI experts (Growth, Finance, Risk) analyzes it independently. A moderator measures where they disagree, and the experts revise their positions after seeing each other's reasoning. An arbiter steps in only when the conflict persists. The output is a structured decision memo that keeps the dissent instead of averaging it away. A human approves the memo before anything leaves the system.

> Disagreement is the product. The memo tells you *where* the experts disagreed and *why*, not just what the consensus was.

---

## How it works

```
Problem statement + optional docs (PDF / TXT / MD)
        │
        ▼
 RAG ingestion ── ephemeral Chroma store + cross-encoder reranking
        │
        ▼
 Turn 1 ── Growth · Finance · Risk agents run in parallel
        │
        ▼
 Moderator ── deterministic disagreement score (0.0 – 1.0)
        ├── < 0.2  ──────────────────────────────┐
        ▼                                         │
 Turn 2 ── peer-aware revision + dissent notes    │
        │                                         │
        ▼                                         │
 Moderator ── re-score                            │
        ├── ≥ 0.7 ──► Arbiter (rules on flagged   │
        │             conflicts only)             │
        ▼                                         ▼
 Synthesizer ── DecisionMemo that preserves dissent
        │
        ▼
 Guardrails ── structural checks + LLM policy check
        │
        ▼
 Human review ── approve · feedback (unlimited rounds) · abandon
        │
        ▼
 Slack webhook on approval
```

The full node-level graph is in [`workflow.mermaid`](workflow.mermaid).

### Key pieces

| Area | What it does | Code |
|------|--------------|------|
| RAG | PDF/TXT/MD extraction, chunking with `RecursiveCharacterTextSplitter`, a per-run in-memory Chroma store, top-8 → top-4 reranking with `ms-marco-MiniLM-L-6-v2` | [`src/rag/`](src/rag), [`src/tools/doc_retrieval.py`](src/tools/doc_retrieval.py) |
| Tools | Tavily web search with retry on 429; a deterministic ROI / NPV / IRR / breakeven calculator | [`src/tools/`](src/tools) |
| Expert agents | Growth, Finance and Risk personas with Pydantic-validated structured output and an auto-retry on schema errors | [`src/agents/`](src/agents) |
| Moderation | Disagreement score from recommendation mismatches, confidence spread and risk-severity divergence | [`src/agents/moderator.py`](src/agents/moderator.py) |
| Arbiter & Synthesizer | Targeted conflict rulings; memo compilation; routing of human feedback to the synthesizer or a specific agent | [`src/agents/arbiter.py`](src/agents/arbiter.py), [`src/agents/synthesiser.py`](src/agents/synthesiser.py) |
| Guardrails | Stage 1 structural validation, stage 2 LLM ethics/policy check | [`src/guardrails/checks.py`](src/guardrails/checks.py) |
| Orchestration | LangGraph workflow with parallel fan-outs, conditional edges and an interrupt for human review | [`src/graph.py`](src/graph.py) |
| API | FastAPI with async background runs and checkpointed interrupt/resume | [`src/api/main.py`](src/api/main.py) |
| Auth & persistence | Google OAuth, JWT sessions, Supabase-backed users and run history | [`src/auth/`](src/auth), [`src/db/`](src/db) |
| Rate limiting | Separate limits for run creation and general requests; cheap polling endpoints are exempt | [`src/middleware/rate_limiter.py`](src/middleware/rate_limiter.py) |
| Frontend | Next.js 14 + Tailwind workspace: query box, live debate feed, memo card, session manager, light/dark themes | [`frontend-next/`](frontend-next) |
| Evaluation | 5 scenarios, each exercising a different exit path (agreement skip, turn 2, arbiter, feedback loop, prompt injection) | [`tests/eval/run_eval.py`](tests/eval/run_eval.py) |

---

## Tech stack

**Backend:** Python, LangGraph, LangChain, FastAPI, Pydantic v2, Chroma, sentence-transformers, Supabase, LangSmith
**LLMs:** provider-agnostic via config (OpenAI, Anthropic, Google GenAI / Vertex AI)
**Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
**Infra:** AWS EC2, nginx, systemd, GitHub Actions

---

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/runs` | Start a run (problem statement + file uploads) |
| `GET` | `/runs/{run_id}/status` | Poll state and timeline |
| `GET` | `/runs` | The current user's run history |
| `POST` | `/runs/{run_id}/review` | Approve, send feedback, or abandon |
| `GET` | `/auth/google/login`, `/auth/google/callback` | Google OAuth |
| `GET/DELETE/POST` | `/api/sessions/me`, `/api/sessions/sessions`, `/api/sessions/sessions/{id}`, `/api/sessions/logout`, `/api/sessions/logout-all` | Session management |

---

## Running locally

### 1. Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in LLM, Google OAuth, Supabase, LangSmith keys
uvicorn src.api.main:app --reload --port 8000
```

Optional keys: `TAVILY_API_KEY` for web search and `SLACK_WEBHOOK_URL` for the approval action.

### 2. Frontend

```bash
cd frontend-next
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE=http://localhost:8000
npm install
npm run dev                  # http://localhost:3000
```

### 3. Tests and evaluation

```bash
pytest tests/
python tests/eval/run_eval.py --scenario all
```

The eval scenarios use a synthetic company corpus (NovaSkin, a D2C skincare brand) in [`synthetic_docs/`](synthetic_docs/README.md).

---

## Deployment

Pushing to the `production` branch triggers [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The workflow connects to an EC2 host over SSH, installs dependencies and restarts the systemd services in [`deploy/`](deploy). Uvicorn runs on `:8000` and Next.js on `:3000`, both behind nginx.

---

## Project layout

```
src/
  agents/       growth, finance, risk, moderator, arbiter, synthesiser
  api/          FastAPI app
  auth/         Google OAuth, JWT, sessions
  db/           Supabase client, user and run stores
  guardrails/   output and policy checks
  hitl/         human review state transitions
  middleware/   rate limiter
  rag/          ingestion and retriever
  tools/        web search, financial calculator, doc retrieval
  graph.py      LangGraph assembly
  schemas.py    shared Pydantic contracts
frontend-next/  Next.js UI
tests/          unit, e2e and eval harness
deploy/         nginx + systemd units
synthetic_docs/ RAG corpus for evals
```

---

## Further reading

| Doc | Contents |
|-----|----------|
| [`PRD_TRD.md`](PRD_TRD.md) | Product and technical requirements: agent specs, schemas, graph design, RAG, guardrails, HITL, evaluation plan, trade-offs |
| [`PLAN.md`](PLAN.md) | Execution plan, task DAG and phase breakdown |
| [`INSTRUCTIONS.md`](INSTRUCTIONS.md) | Working conventions: branching, commits, schema rules |
| [`contributions.md`](contributions.md) | Breakdown by track (A–D) and a full architecture diagram |
| [`src/tools/README.md`](src/tools/README.md) | Integration contracts for the shared tools |
| [`synthetic_docs/README.md`](synthetic_docs/README.md) | Index of the synthetic company corpus |
| [`trace.md`](trace.md) | Development trace log |
