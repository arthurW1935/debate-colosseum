# Debate Colosseum — Execution Plan

> Read alongside PRD_TRD.md and INSTRUCTIONS.md.  
> Tasks are ordered by dependency, not by calendar. Work items within the same phase can be picked up in parallel by whoever is free.

---

## How to read this file

- Each task has an ID (e.g. `A3`), a commit message, the files it touches, and a "depends on" field.
- **Depends on: —** means you can start immediately after the bootstrap phase.
- Tasks with the same dependencies can be worked in parallel.
- The task DAG at the bottom is the single source of truth for sequencing.

Rule: **`main` never breaks.** Feature branch → PR → merge. If your node crashes the graph, fix it before merging.

---

## Phase 0 — Bootstrap (all 4, do together first)

These produce the shared contracts everyone else builds against. Nothing else can start until these are merged.

| ID | Commit | Output | Owner |
|----|--------|--------|-------|
| P0-1 | `chore: project scaffold — repo structure, .env.example, requirements.txt` | Folder structure (see below) | All |
| P0-2 | `feat: shared pydantic schemas — ExpertAnalysis, DisagreementReport, ArbitrationResult, DecisionMemo, GraphState` | `src/schemas.py` | All |
| P0-3 | `feat: mock fixtures for each schema` | `tests/fixtures/*.json` | All |
| P0-4 | `chore: config + LangSmith project init` | `src/config.py`, LangSmith project live | All |

### Repo structure

```
debate-colosseum/
├── src/
│   ├── schemas.py
│   ├── config.py
│   ├── graph.py              # wired last, in Phase 4
│   ├── agents/
│   │   ├── growth.py
│   │   ├── finance.py
│   │   ├── risk.py
│   │   ├── moderator.py
│   │   ├── arbiter.py
│   │   └── synthesizer.py
│   ├── tools/
│   │   ├── web_search.py
│   │   ├── financial_calc.py
│   │   └── doc_retrieval.py
│   ├── rag/
│   │   ├── ingest.py
│   │   └── retriever.py
│   ├── guardrails/
│   │   └── checks.py
│   ├── hitl/
│   │   └── review.py
│   └── api/
│       └── main.py
├── frontend/
│   └── app.py
├── tests/
│   ├── fixtures/
│   └── eval/
├── logs/
├── .env.example
├── requirements.txt
├── PRD_TRD.md
├── plan.md
└── INSTRUCTIONS.md
```

---

## Phase 1 — Independent tracks (A, B, C, D in parallel)

All four people work simultaneously. Each track builds against mock fixtures until Phase 2 wires them together.

---

### Track A — RAG pipeline & shared tools
**Owner: Person A**  
**Integration contract:** `ingest_context(state) → state` with `state.retriever` populated; `doc_retrieval(query, retriever) → list[str]`; `web_search(query) → list[dict]`

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| A1 | `feat: file upload handler — PDF + plain text extraction` | `src/rag/ingest.py` | P0-1 |
| A2 | `feat: text chunker — RecursiveCharacterTextSplitter, 600 tokens, 80 overlap` | `src/rag/ingest.py` | A1 |
| A3 | `feat: embedding + chroma in-memory vector store` | `src/rag/ingest.py` | A2 |
| A4 | `feat: doc_retrieval tool — cosine similarity top-8, cross-encoder rerank to top-4` | `src/tools/doc_retrieval.py` | A3 |
| A5 | `feat: ingest_context LangGraph node — wires into GraphState` | `src/rag/ingest.py` | A4, P0-2 |
| A6 | `feat: graceful no-docs fallback — retriever is None, agents skip retrieval` | `src/tools/doc_retrieval.py` | A5 |
| A7 | `feat: web_search tool — Tavily integration, top 5 results` | `src/tools/web_search.py` | P0-1 |
| A8 | `test: ingest pipeline — verify chunks, index, retrieval, reranking` | `tests/test_rag.py` | A4 |
| A9 | `test: web_search — verify real query returns structured results` | `tests/test_tools.py` | A7 |
| A10 | `test: full ingest node with mock GraphState` | `tests/test_ingest_node.py` | A5, A6 |
| A11 | `docs: tool contracts for Person B` | `src/tools/README.md` | A9, A10 |

> A8, A9 can run in parallel with each other. A11 is the signal to B that tools are ready to wire in.

---

### Track B — Expert agents (turns 1 & 2)
**Owner: Person B**  
**Integration contract:** `expert_{role}(state) → state` with `state.turn1_analyses[role]` and `state.turn2_analyses[role]` populated; all outputs schema-valid against `ExpertAnalysis`

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| B1 | `feat: growth agent — system prompt, LLM call, ExpertAnalysis output` | `src/agents/growth.py` | P0-2 |
| B2 | `feat: finance agent — system prompt, ExpertAnalysis output` | `src/agents/finance.py` | P0-2 |
| B3 | `feat: risk agent — system prompt, ExpertAnalysis output` | `src/agents/risk.py` | P0-2 |
| B4 | `feat: financial_calculator tool — ROI, NPV, IRR, breakeven` | `src/tools/financial_calc.py` | P0-1 |
| B5 | `test: all three agents with mocked tools — verify ExpertAnalysis schema` | `tests/test_agents_t1.py` | B1, B2, B3 |
| B6 | `feat: schema validation + retry wrapper on all agent outputs` | `src/agents/*.py` | B5 |
| B7 | `feat: turn 2 peer context injection — each agent receives peers' turn-1 outputs` | `src/agents/*.py` | B6 |
| B8 | `test: turn 2 agents — verify dissent_notes populated on disagreement` | `tests/test_agents_t2.py` | B7 |

> B1, B2, B3, B4 can all start in parallel. B5 waits for all three agents. Wire real tools in Phase 2 (B9).

---

### Track C — Judgment chain (moderator, arbiter, synthesizer, guardrails)
**Owner: Person C**  
**Integration contract:** `moderator(state) → state`; `arbiter(state) → state`; `synthesizer(state) → state`; `guardrail_check(state) → state`; all outputs schema-valid

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| C1 | `feat: disagreement scorer — recommendation mismatch + confidence variance + risk tier divergence → 0–1 score` | `src/agents/moderator.py` | P0-2 |
| C2 | `feat: moderator LLM call — DisagreementReport with human-readable summary of flagged points` | `src/agents/moderator.py` | C1 |
| C3 | `feat: routing thresholds — score < 0.2 → synthesis; ≥ 0.2 → turn 2; ≥ 0.7 post-turn-2 → arbiter` | `src/agents/moderator.py` | C2 |
| C4 | `test: moderator — verify score and routing for all three paths using fixtures` | `tests/test_moderator.py` | C3 |
| C5 | `feat: arbiter agent — rules on flagged DisagreementPoints only, ArbitrationResult output` | `src/agents/arbiter.py` | P0-2 |
| C6 | `feat: synthesizer agent — DecisionMemo with preserved dissent and optional arbitration summary` | `src/agents/synthesizer.py` | P0-2 |
| C7 | `test: synthesizer — verify dissent_notes surface in memo, arbitration_summary present when arbiter ran` | `tests/test_synthesizer.py` | C6 |
| C8 | `feat: guardrail_check — schema validation + rule-based policy checks (non-empty risks, next_steps, summary length)` | `src/guardrails/checks.py` | P0-2 |
| C9 | `feat: guardrail_check — LLM-based ethical/legal policy check` | `src/guardrails/checks.py` | C8 |
| C10 | `test: guardrails — passing memo, blocked memo, incomplete memo` | `tests/test_guardrails.py` | C9 |

> C1→C2→C3→C4 are sequential. C5, C6, C8 can all start from P0-2 in parallel with the moderator chain.

---

### Track D — App, HITL, action executor, eval harness
**Owner: Person D**  
**Integration contract:** FastAPI at `POST /runs`, `GET /runs/{id}/status`, `POST /runs/{id}/review`; Streamlit renders full UI; eval harness runs all 5 scenarios via `python tests/eval/run_eval.py`

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| D1 | `feat: FastAPI skeleton — POST /runs, GET /runs/{id}/status` | `src/api/main.py` | P0-1 |
| D2 | `feat: SQLite checkpointer + run_id generation` | `src/api/main.py` | D1 |
| D3 | `feat: HITL endpoint — POST /runs/{id}/review, resumes graph from checkpoint` | `src/api/main.py`, `src/hitl/review.py` | D2 |
| D4 | `feat: action_executor — Slack webhook fires on approval` | `src/api/main.py` | D3 |
| D5 | `feat: Streamlit skeleton — problem input form + file upload` | `frontend/app.py` | P0-1 |
| D6 | `feat: Streamlit debate timeline — polls status, shows per-node outputs as they arrive` | `frontend/app.py` | D5 |
| D7 | `feat: Streamlit memo review UI — renders all DecisionMemo sections` | `frontend/app.py` | D6 |
| D8 | `feat: Streamlit HITL controls — approve / edit / reject wired to API` | `frontend/app.py` | D7, D3 |
| D9 | `feat: LangSmith trace decorator on all nodes` | `src/config.py`, all agent files | P0-4 |
| D10 | `feat: eval harness — runs all 5 scenarios, logs outputs + routing path + scores` | `tests/eval/run_eval.py` | — |

> D1→D2→D3→D4 are sequential (backend). D5→D6→D7→D8 are sequential (frontend). Both chains start from P0-1 independently. D9 and D10 can start any time.

---

## Phase 2 — Cross-track wiring (B × A, then C × B)

These tasks connect the independent tracks. Start as soon as their prerequisites merge.

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| X1 | `feat: wire real tools into agents — web_search, doc_retrieval, financial_calc` | `src/agents/*.py` | A11, B8 |
| X2 | `test: agents with real tools on scenario 1 problem statement` | `tests/test_agents_e2e.py` | X1, A10 |
| X3 | `feat: wire moderator against real agent outputs — smoke test all three routing paths` | `src/agents/moderator.py` | X2, C4 |
| X4 | `feat: wire synthesizer + guardrails against real memo — smoke test pass and block` | `src/agents/synthesizer.py`, `src/guardrails/checks.py` | X3, C10 |

---

## Phase 3 — Full graph assembly

All tracks must be merged before this phase starts. Person C leads; everyone else is available for fixes.

| ID | Commit | Files | Depends on |
|----|--------|-------|------------|
| I1 | `feat: full LangGraph graph — all nodes, edges, conditional routing, interrupt` | `src/graph.py` | X4, D3 |
| I2 | `fix: schema mismatches found during wiring` | wherever broken | I1 |
| I3 | `test: e2e run of scenario 1 — EU expansion (full debate path)` | `tests/eval/` | I2 |
| I4 | `test: e2e run of scenario 2 — discount campaign (consensus early exit)` | `tests/eval/` | I2 |
| I5 | `test: e2e run of scenario 3 — competitor acquisition (arbiter trigger)` | `tests/eval/` | I2 |
| I6 | `test: e2e run of scenario 4 — early hiring with RAG docs` | `tests/eval/` | I2 |
| I7 | `test: e2e run of scenario 5 — prompt injection (guardrail block)` | `tests/eval/` | I2 |

> I3–I7 can all run in parallel once I2 is merged.

---

## Phase 4 — Polish and ship

Start only after all 5 eval scenarios pass.

| Task | Owner |
|------|-------|
| Fix any failing eval cases | Owner of that node |
| Tighten prompt quality on weakest agent | Person B |
| Polish Streamlit UI for demo | Person D |
| Write individual contribution docs (`contributions/{name}.md`) | Each person |
| Dry-run the 10-minute demo twice end-to-end | All |
| Tag `v1.0.0` | All |

---

## Post-MVP Roadmap

Only after `v1.0.0` is tagged. Ordered by effort, lowest first.

### PM-A — Persistent global doc pool with per-agent subsets
**Owner: Person A**

| ID | Commit | Files |
|----|--------|-------|
| PM-A1 | `feat: swap in-memory Chroma for persistent disk-backed collection` | `src/rag/ingest.py` |
| PM-A2 | `feat: doc tagging schema — category, agent_roles, source` | `src/schemas.py`, `src/rag/ingest.py` |
| PM-A3 | `feat: per-agent retrieval filter — only fetch chunks tagged for that role` | `src/tools/doc_retrieval.py` |
| PM-A4 | `feat: admin endpoints — POST /docs, DELETE /docs/{id}` | `src/api/main.py` |
| PM-A5 | `feat: Streamlit admin panel — upload to global pool, tag by role` | `frontend/app.py` |

### PM-B — User-configurable/custom agent rosters
**Owner: Person B**

| ID | Commit | Files |
|----|--------|-------|
| PM-B1 | `feat: role config schema — name, brief, tools_allowed` | `src/schemas.py` |
| PM-B2 | `feat: dynamic agent factory — instantiates agent node from role config` | `src/agents/factory.py` |
| PM-B3 | `feat: Streamlit role builder UI — add/edit/remove roles before run` | `frontend/app.py` |
| PM-B4 | `test: custom role (Legal) — verify ExpertAnalysis schema and disagreement score still valid` | `tests/test_custom_roles.py` |

### PM-C — Agent-to-agent clarification Q&A
**Owner: Person C + B**

| ID | Commit | Files |
|----|--------|-------|
| PM-C1 | `feat: ClarificationRequest + ClarificationResponse schemas` | `src/schemas.py` |
| PM-C2 | `feat: turn 2 Q&A sub-graph — asking agent emits one question, target responds once` | `src/agents/clarification.py` |
| PM-C3 | `feat: wire Q&A sub-graph into turn 2 fan-out — fires before peer-aware revision` | `src/graph.py` |
| PM-C4 | `feat: termination guard — max 1 question per agent per round enforced in state` | `src/agents/clarification.py` |
| PM-C5 | `test: Q&A sub-graph — question/response logged and incorporated into turn 2 output` | `tests/test_clarification.py` |

---

## Task DAG

```
P0-1 ──┬──────────────────────────────────────────────────────────┐
       │                                                          │
P0-2 ──┼──┬── B1 ──┐                                             │
       │  │        ├── B5 ── B6 ── B7 ── B8 ──────────── X1 ──── X2 ── X3 ── X4 ── I1
       │  ├── B2 ──┤                                    ↑
       │  ├── B3 ──┘                                    │
       │  │                                             │
       │  ├── C1 ── C2 ── C3 ── C4 ─────────────── X3 ─┤
       │  ├── C5 ─────────────────────────────────────  │
       │  ├── C6 ── C7 ─────────────────────────── X4 ──┘
       │  └── C8 ── C9 ── C10 ─────────────────────────┘
       │
P0-1 ──┼── A1 ── A2 ── A3 ── A4 ── A5 ── A6 ── A11 ─────────── X1
       │                            └── A8
       │                  A7 ── A9 ─────────────────────────────── X1
       │
P0-1 ──┴── D1 ── D2 ── D3 ── D4
           D5 ── D6 ── D7 ── D8
           D9 (any time)
           D10 (any time)

X4 + D3 ──► I1 ── I2 ── I3..I7 (parallel) ──► Phase 4 ──► v1.0.0
```



---

## Detailed Task Specifications

This section expands on the tasks listed in the tables above, providing technical implementation details, required inputs/outputs, and acceptance criteria for each item.

### Phase 0: Bootstrap

#### P0-1: Project Scaffold
- **Owner:** All
- **Files:** Repo root, `.env.example`, `requirements.txt`
- **Implementation:** Create the directory structure `src/agents`, `src/tools`, `src/rag`, `src/guardrails`, `src/hitl`, `src/api`, `frontend`, `tests/fixtures`, `tests/eval`. Create `requirements.txt` with LangGraph, Streamlit, FastAPI, Pydantic, Anthropic, Tavily-python, ChromaDB, pytest.
- **Acceptance:** Folder structure matches the layout in Phase 0 section.

#### P0-2: Shared Pydantic Schemas
- **Owner:** All
- **Files:** `src/schemas.py`
- **Implementation:** Define `Recommendation`, `RiskItem`, `ExpertAnalysis`, `DisagreementPoint`, `DisagreementReport`, `ArbitrationResult`, `SynthesizerFeedbackDecision`, `HumanFeedbackEntry`, `DecisionMemo`, `GraphState`. Ensure all fields use type hints and Pydantic v2 `Field` where validation (e.g., ge=0.0, le=1.0) is needed.
- **Acceptance:** Code parses correctly, `GraphState` contains all necessary state keys.

#### P0-3: Mock Fixtures
- **Owner:** All
- **Files:** `tests/fixtures/*.json`
- **Implementation:** Create valid JSON examples for each Pydantic schema defined in P0-2.
- **Acceptance:** `Model.model_validate_json()` works for each fixture.

#### P0-4: Config & LangSmith
- **Owner:** All
- **Files:** `src/config.py`
- **Implementation:** Set up environment variable loading using `dotenv`. Initialize LangSmith tracing context, ensuring `LANGSMITH_PROJECT=debate-colosseum`.
- **Acceptance:** Application starts without error if `.env` is properly populated.

### Phase 1: Independent Tracks

#### Track A: RAG & Tools

##### A1: File Upload Handler
- **Owner:** Person A
- **Files:** `src/rag/ingest.py`
- **Implementation:** Write a function to accept uploaded files (PDF, txt, md). Use PyPDF2 to extract text from PDFs.
- **Acceptance:** Successfully extracts raw text string from valid and multi-page PDFs.

##### A2: Text Chunker
- **Owner:** Person A
- **Files:** `src/rag/ingest.py`
- **Implementation:** Initialize `RecursiveCharacterTextSplitter` with `chunk_size=600` and `chunk_overlap=80`.
- **Acceptance:** Converts extracted text into lists of chunks.

##### A3: Embedding & Vector Store
- **Owner:** Person A
- **Files:** `src/rag/ingest.py`
- **Implementation:** Connect `text-embedding-3-small` or `all-MiniLM-L6-v2`. Create an in-memory Chroma collection per run. Tag chunks with source info.
- **Acceptance:** Returns a queryable `Chroma` instance.

##### A4: Doc Retrieval Tool
- **Owner:** Person A
- **Files:** `src/tools/doc_retrieval.py`
- **Implementation:** Create a LangChain retriever. On query, do cosine similarity for top 8, then use `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank to top 4.
- **Acceptance:** Precision test: reranked results are ordered closer to ground truth context than raw cosine search.

##### A5: `ingest_context` LangGraph Node
- **Owner:** Person A
- **Files:** `src/rag/ingest.py`
- **Signature:** `def ingest_context(state: GraphState) -> GraphState`
- **Implementation:** Combines A1-A3. Given `state.context_docs`, builds the Chroma collection and populates `state.retriever`.
- **Acceptance:** State mutation is non-destructive, `state.retriever` is successfully attached.

##### A6: Graceful No-Docs Fallback
- **Owner:** Person A
- **Files:** `src/tools/doc_retrieval.py`
- **Implementation:** If `state.retriever` is None, return an empty list immediately without erroring.
- **Acceptance:** Tool returns `[]` when no docs are provided.

##### A7: Web Search Tool
- **Owner:** Person A
- **Files:** `src/tools/web_search.py`
- **Implementation:** Wrap Tavily API. Input is a string. Return list of dicts `{title, url, snippet}`. Retry once on HTTP 429.
- **Acceptance:** Returns top 5 external links with correct schema.

##### A8-A11: Track A Testing & Docs
- **Implementation:** Write pytest cases mocking external tools if needed, verifying chunks and schemas. Update `src/tools/README.md` defining inputs/outputs for Track B.

#### Track B: Expert Agents

##### B1: Growth Agent
- **Owner:** Person B
- **Files:** `src/agents/growth.py`
- **Signature:** `def expert_growth(state: GraphState) -> GraphState`
- **Implementation:** System prompt focuses on market opportunity, competitive positioning. LLM call outputs `ExpertAnalysis`. Update `state.turn1_analyses["growth"]`. Bind `web_search` and `doc_retrieval`. Wrap with validation retry logic.
- **Acceptance:** Returns valid `ExpertAnalysis` on Turn 1.

##### B2: Finance Agent
- **Owner:** Person B
- **Files:** `src/agents/finance.py`
- **Signature:** `def expert_finance(state: GraphState) -> GraphState`
- **Implementation:** System prompt focuses on ROI, cash flow. Binds `financial_calc` and `doc_retrieval`. Update `state.turn1_analyses["finance"]`.
- **Acceptance:** Returns valid `ExpertAnalysis`.

##### B3: Risk Agent
- **Owner:** Person B
- **Files:** `src/agents/risk.py`
- **Signature:** `def expert_risk(state: GraphState) -> GraphState`
- **Implementation:** System prompt focuses on operational, legal, market risks. Binds `web_search` and `doc_retrieval`. Update `state.turn1_analyses["risk"]`.
- **Acceptance:** Returns valid `ExpertAnalysis` with properly scoped `RiskItem` list.

##### B4: Financial Calculator Tool
- **Owner:** Person B
- **Files:** `src/tools/financial_calc.py`
- **Implementation:** Deterministic Python functions for ROI, NPV, IRR, breakeven based on inputs (principal, rate, periods, cash flows).
- **Acceptance:** Correct math results. E.g. IRR handles negative starting flow and positive subsequent flows.

##### B5-B6: Track B Testing & Schema Wrapper
- **Implementation:** Build the try/except loop to catch validation failures, add the correction prompt, and attempt 1 retry before raising. Verify all agents with mock tools.

##### B7: Turn 2 Peer Context Injection
- **Owner:** Person B
- **Files:** `src/agents/*.py`
- **Implementation:** If `state.current_turn == 2`, agent prompt receives peers' Turn 1 `ExpertAnalysis` and the `DisagreementReport`. Agent updates `state.turn2_analyses[role]` and populates `dissent_notes`.
- **Acceptance:** Agent can explicitly name a peer's assumption it disagrees with.

##### B8: Track B Turn 2 Tests
- **Implementation:** Test turn 2 logic. Verify `dissent_notes` are populated.

#### Track C: Judgment Chain

##### C1: Disagreement Scorer
- **Owner:** Person C
- **Files:** `src/agents/moderator.py`
- **Implementation:** Function parsing all three `ExpertAnalysis`. 
  - Compare recommendation labels (±0.3 per mismatch). 
  - Compare confidence (std dev). 
  - Compare risk tier divergence.
  - Return float `0.0 - 1.0`.
- **Acceptance:** Correctly computes 0.0 for unanimous identical fields, >0.7 for divergent fields.

##### C2: Moderator LLM Call
- **Owner:** Person C
- **Files:** `src/agents/moderator.py`
- **Signature:** `def moderator(state: GraphState) -> GraphState`
- **Implementation:** If score > 0, call LLM to generate human-readable `summary` and `flagged_points` (`DisagreementReport`).
- **Acceptance:** Outputs accurate `DisagreementReport`.

##### C3: Routing Thresholds
- **Owner:** Person C
- **Implementation:** Implement routing logic (score < 0.2 synthesis; >= 0.2 turn 2; >= 0.7 arbiter). Assign to `DisagreementReport.route_decision`.

##### C4: Track C Moderator Tests
- **Implementation:** Mock three different scenarios of agent analyses to assert <0.2, 0.2-0.7, and >0.7 scores.

##### C5: Arbiter Agent
- **Owner:** Person C
- **Files:** `src/agents/arbiter.py`
- **Signature:** `def arbiter(state: GraphState) -> GraphState`
- **Implementation:** System prompt instructs strictly ruling on `DisagreementReport.flagged_points`. No tools. Output `ArbitrationResult`.
- **Acceptance:** Valid `ArbitrationResult` with specific rulings on provided topics.

##### C6: Synthesizer Agent
- **Owner:** Person C
- **Files:** `src/agents/synthesizer.py`
- **Signature:** `def synthesizer(state: GraphState) -> GraphState`
- **Implementation:** Combines final expert analyses and arbitration result. Outputs `DecisionMemo`. When `state.current_feedback_text` is set, processes human feedback according to PRD F8 rules (output `SynthesizerFeedbackDecision`).
- **Acceptance:** `DecisionMemo` successfully preserves dissent if unresolved.

##### C7-C10: Synthesizer & Guardrails
- **Files:** `src/guardrails/checks.py`
- **Signature:** `def guardrail_check(state: GraphState) -> GraphState`
- **Implementation:** Rule checks: Enums, non-empty risk/next steps. LLM check: "Is this illegal/unethical?". 
- **Acceptance:** Properly blocks and annotates `state.guardrail_passed = False` for prompt injection or empty lists.

#### Track D: App, HITL, Eval

##### D1-D4: Backend API & Checkpointing
- **Owner:** Person D
- **Files:** `src/api/main.py`, `src/hitl/review.py`
- **Implementation:** FastAPI. Integrate LangGraph `MemorySaver` or `SqliteSaver`. Endpoints: `POST /runs`, `GET /runs/{id}/status`, `POST /runs/{id}/review`. Implement `action_executor` firing Slack webhook if approved.
- **Acceptance:** API correctly starts, pauses at interrupt, and resumes on POST.

##### D5-D8: Streamlit Frontend
- **Owner:** Person D
- **Files:** `frontend/app.py`
- **Implementation:** Single page UI. Problem input. Polls `GET /status`. Displays live Timeline. Renders Decision Memo sections. Approve/Edit/Reject buttons.
- **Acceptance:** Fully functional end-to-end UI against backend.

##### D9-D10: Observability & Eval Harness
- **Owner:** Person D
- **Files:** `tests/eval/run_eval.py`
- **Implementation:** Script calling the graph directly (bypassing FastAPI) with 5 hardcoded scenarios. Save JSON outputs to `logs/eval_results/`. Ensure `@traceable` applied.

### Phase 2: Cross-Track Wiring

#### X1-X2: Tools to Agents
- **Owner:** B & A
- **Implementation:** Replace mock tools in `src/agents/*.py` with real `src/tools/*.py`. Run e2e for Turn 1 logic.

#### X3-X4: Judgment Chain Smoke Tests
- **Owner:** C & B
- **Implementation:** Pass real agent outputs into Moderator and Synthesizer to verify edge cases (token limits, strange RAG outputs).

### Phase 3: Full Graph Assembly

#### I1-I2: LangGraph Wiring
- **Owner:** Person C (Driver), All
- **Files:** `src/graph.py`
- **Implementation:** Use `StateGraph(GraphState)`. Add all nodes. Add conditional edges based on moderator and human review. Compile with checkpointer. 
- **Acceptance:** Can `graph.invoke()` from start to interrupt.

#### I3-I7: End-to-End Scenarios
- **Owner:** All
- **Implementation:** Execute 5 eval cases. Fix schema mismatches and prompt weirdness. 
- **Acceptance:** All 5 pass.
