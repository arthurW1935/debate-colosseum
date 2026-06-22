# Debate Colosseum — PRD + TRD

> Multi-Agent Business Decision Platform  
> Course: Multi-Agent Orchestration [AI/ML] — Capstone Project  
> Team size: 4

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Problem Statement](#2-problem-statement)
3. [Target Users](#3-target-users)
4. [Goals and Non-Goals](#4-goals-and-non-goals)
5. [Success Metrics](#5-success-metrics)
6. [User Flow](#6-user-flow)
7. [Feature Specification (PRD)](#7-feature-specification-prd)
8. [System Architecture (TRD)](#8-system-architecture-trd)
9. [Agent Specifications](#9-agent-specifications)
10. [Data Schemas (Pydantic)](#10-data-schemas-pydantic)
11. [LangGraph State and Graph Design](#11-langgraph-state-and-graph-design)
12. [Tool Specifications](#12-tool-specifications)
13. [RAG Pipeline](#13-rag-pipeline)
14. [Guardrails and Safety](#14-guardrails-and-safety)
15. [Human-in-the-Loop](#15-human-in-the-loop)
16. [Evaluation Plan](#16-evaluation-plan)
17. [Observability](#17-observability)
18. [Tech Stack](#18-tech-stack)
19. [Tradeoffs Considered](#19-tradeoffs-considered)

---

## 1. Product Overview

Debate Colosseum is a multi-agent AI platform for complex business decisions. A user describes a decision they need to make. A panel of specialist AI agents independently analyzes the problem, a moderator surfaces where they genuinely disagree, disagreeing agents get a peer-aware second round to revise or defend their position, and an arbiter steps in only when disagreement persists. A synthesizer produces a structured decision memo that preserves dissent rather than flattening it. A human reviews and approves before anything is sent externally.

**Core differentiator:** disagreement is the product, not noise to be averaged away. The memo is useful precisely because it tells you *where* experts disagreed and *why*, not just what a consensus opinion is.

---

## 2. Problem Statement

Business decisions are often made with a single LLM prompt that returns one confident-sounding perspective. This hides uncertainty, suppresses minority viewpoints, and gives no way to know whether important angles were considered. Debate Colosseum forces independent analysis, structured disagreement, and transparent conflict resolution before a human sees any recommendation.

---

## 3. Target Users

- Founders and operators making high-stakes calls (pricing, hiring, market expansion, pivots)
- Investment analysts stress-testing a thesis before a decision
- Strategy teams who need a structured record of deliberation, not just a bottom line

---

## 4. Goals and Non-Goals

### MVP Goals

- Accept a problem statement + optional context documents
- Run 3 expert agents (Growth, Finance, Risk) in parallel, each producing a structured independent analysis
- Moderator checks for meaningful disagreement after turn 1; skips to synthesis if agents largely agree
- Turn 2: each agent sees the others' turn-1 positions and revises or defends; moderator re-checks
- Turn 3 (Arbiter): fires only when significant disagreement persists after turn 2; rules on specific flagged points, does not repeat the full debate
- Synthesizer produces a structured `DecisionMemo` that preserves dissent
- Guardrails validate all outputs and run a policy check on the memo
- Human reviews the memo with unlimited feedback cycles — each round of feedback triggers one re-processing pass before returning for review
- Feedback routes to Synthesizer first; only escalates to a targeted agent re-run if the Synthesizer determines agent-level revision is needed; a lightweight peer contradiction check fires if a targeted agent changes its position
- Approval triggers one real external action (Slack or email)
- Cross-encoder reranking on retrieved RAG chunks before injection into agent prompts
- LangSmith tracing on every node
- 5+ evaluation scenarios, each exercising a different exit path

### Non-Goals (explicitly out of scope for MVP)

- Open-ended multi-turn chat with the user
- More than one external action integration
- Production auth, multi-tenancy, billing
- Large-scale production vector database

### Post-MVP Good-to-Haves

These are intentionally deferred — not because they are bad ideas, but because they each add meaningful complexity that would risk the core pipeline in the available time. Build these after the MVP is stable and all 5 eval scenarios pass cleanly.

**1. User-configurable/custom agent rosters**
Let users define their own expert roles (e.g. Legal, Marketing, Engineering) with a custom brief. The prompt swap itself is trivial, but every new role needs tested prompts, a calibrated contribution to the disagreement score, and schema-valid outputs. One misconfigured custom agent silently degrades the memo quality with no safety net. Needs: role config UI, a prompt template system, and a lightweight eval harness per new role before it can be trusted.

**2. Persistent global doc pool with per-agent subsets**
Two-tier document architecture: session docs scoped to the run (already built), plus a company-wide persistent doc pool where each agent role has access to a configured subset (e.g. Finance sees all finance docs, Risk sees compliance docs but not finance). Needs: persistent vector store (swap in-memory Chroma for a disk-backed or hosted one), a doc tagging/categorization layer, per-agent filter config, and an admin UI for adding/removing docs. The per-agent filtering is the riskiest piece — a miscategorized doc gives an agent wrong context with no visible error.

**3. Agent-to-agent clarification Q&A**
During turn 2, an agent can direct one targeted question to a specific peer (e.g. Risk asks Finance: "What discount rate did you assume?"), the peer responds once, and the asking agent incorporates the answer before finalizing its round-2 output. Needs: a structured Q&A sub-protocol with a new message schema, turn-taking logic, and a termination rule — effectively a mini sub-graph within the turn-2 fan-out. High signal value for demos, but the highest implementation complexity of the three.

---

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| End-to-end completeness | All 5 eval cases run without crashing; every node produces schema-valid output |
| Disagreement detection | Round 2 triggers on 4/5 scenarios designed to conflict; skips correctly on 1/5 agreement scenario |
| Turn 3 (Arbiter) trigger | Fires correctly on 1 adversarial scenario designed to survive turn 2 |
| Memo quality | Average ≥ 3.5/5 across test cases on: clarity, risk surfacing, dissent preservation |
| Guardrail effectiveness | 0 malformed outputs reach the human unhandled |
| E2E latency | Full run (including possible turn 3) under 2 minutes |
| HITL correctness | Approval reliably triggers the external action; rejection saves edits only |

---

## 6. User Flow

```
User: enters problem statement + optional context docs
  ↓
System: ingests + indexes context docs (if any)
  ↓
Turn 1: Growth, Finance, Risk agents analyze independently (parallel)
  ↓
Moderator: computes disagreement score
  ├── Score < 0.2  →  skip to Synthesizer
  └── Score ≥ 0.2  →  Turn 2
       ↓
Turn 2: each agent sees peers' turn-1 outputs and revises/defends
  ↓
Moderator: recomputes disagreement score
  ├── Score < 0.7  →  Synthesizer
  └── Score ≥ 0.7  →  Turn 3 (Arbiter)
       ↓
Turn 3: Arbiter rules on specific flagged disputes
  ↓
Synthesizer: produces DecisionMemo (with preserved dissent)
  ↓
Guardrail: schema + policy check
  ↓
Human review: Approve / Feedback / Abandon
  ├── Approve    →  send memo (Slack or email)
  ├── Abandon    →  save state, no external action
  └── Feedback   →  Synthesizer (attempts memo revision from existing analyses)
                      ├── Feedback resolved by Synthesizer alone  →  Guardrail  →  Human review
                      └── Agent revision needed  →  targeted agent re-runs (feedback round)
                              ↓
                          Lightweight peer contradiction check
                              ├── No contradiction  →  Synthesizer  →  Guardrail  →  Human review
                              └── Contradiction detected  →  affected peers get one short revision
                                      ↓
                                  Synthesizer  →  Guardrail  →  Human review
                                  (loop repeats for every new feedback, no cap)
```

---

## 7. Feature Specification (PRD)

### F1 — Problem Input

- Single free-text field for the problem statement (no length limit; 50–500 words typical)
- Optional multi-file upload: PDF and plain text/markdown only for MVP
- UI shows a preview of uploaded files before submission
- User can submit without documents; RAG is simply skipped in that case

### F2 — Expert Analysis (Turn 1)

- Three agents run in parallel: Growth, Finance, Risk
- Each agent receives: system prompt defining its role, the problem statement, any RAG-retrieved context chunks
- Each agent returns a structured `ExpertAnalysis` object (see schema section)
- Finance agent additionally calls the financial calculator tool for quantitative estimates
- Growth and Risk agents may call web search for current market/risk data

### F3 — Moderator and Disagreement Scoring

- Takes all three `ExpertAnalysis` objects as input
- Computes a single disagreement score (0.0–1.0) using a deterministic heuristic:
  - Recommendation label mismatch (proceed / proceed-with-caution / do-not-proceed): ±0.3 per pair
  - Confidence variance across agents: normalized standard deviation
  - Risk severity divergence: compare risk tier labels across agents
- Produces a `DisagreementReport` listing specific points of conflict for use by agents in turn 2 and by the arbiter in turn 3
- Decision thresholds:
  - Score < 0.2 → route to Synthesizer (consensus)
  - 0.2 ≤ score < 0.7 → route to Turn 2
  - Score ≥ 0.7 (after turn 2) → route to Arbiter

### F4 — Turn 2: Peer-Aware Revision

- Each agent receives its own turn-1 analysis, all peers' turn-1 analyses, and the moderator's `DisagreementReport`
- Agent may revise its recommendation or maintain its stance with explicit justification
- Returns a new `ExpertAnalysis` object tagged `round=2`
- Moderator re-scores; if score drops below 0.7, routes to Synthesizer

### F5 — Turn 3: Arbiter

- Fires only when post-turn-2 disagreement score ≥ 0.7
- Receives the `DisagreementReport` listing specific flagged disputes
- Does not re-run a full analysis; it rules only on the listed points
- Returns an `ArbitrationResult` naming which position it sides with on each dispute and why
- Routes to Synthesizer immediately after

### F6 — Synthesizer

- Receives all expert analyses (final round), the `DisagreementReport`, and the `ArbitrationResult` (if any)
- Produces a `DecisionMemo` with sections: executive summary, recommendation, individual expert positions, key disagreements and how they were resolved (or preserved if not resolved), risk register, suggested next steps
- Dissent that was not resolved by the arbiter is explicitly preserved in the memo, not flattened

### F7 — Guardrails

- Schema validation: every node output is validated against its Pydantic schema; on failure, the node retries once with an explicit correction prompt before raising
- Policy check on `DecisionMemo` before human review:
  - Blocks memos recommending anything illegal, discriminatory, or clearly unethical
  - Flags memos with no risk section as incomplete
  - Flags memos with missing "next steps" section
- Guardrail failures are logged and shown to the user as a system error, not silently swallowed

### F8 — Human Review and Feedback Loop

- Memo displayed in the UI with all sections visible
- Three actions: **Approve**, **Feedback**, **Abandon**
  - **Approve** — triggers the external action; run ends
  - **Feedback** — human types a note ("you missed the headcount dependency", "re-check Finance's discount rate"); graph re-enters processing; UI shows the feedback round status before returning the revised memo for review; no cap on feedback cycles
  - **Abandon** — saves run state and memo, no external action; run ends
- The LangGraph interrupt/resume pattern pauses the graph at `human_review`; on Feedback, the graph resumes and loops back through processing before re-interrupting at `human_review` with the revised memo
- Each feedback cycle follows this routing:
  1. **Synthesizer-first check** — Synthesizer receives the current memo + feedback note; attempts to revise without touching any agent. If it can resolve the feedback from existing analyses, it produces a revised `DecisionMemo` and routes to Guardrail. This handles framing, tone, missing context that was already in the data.
  2. **Targeted agent re-run** — If the Synthesizer flags that the feedback requires an agent to revise (it explicitly outputs `requires_agent_revision: true` and `target_agent: str`), only that agent re-runs with the feedback injected. Produces an `ExpertAnalysis` tagged `round="feedback"`.
  3. **Lightweight peer contradiction check** — Moderator runs a narrow diff: does the revised agent analysis contradict anything the other agents said in their final round? If no contradiction, routes directly to Synthesizer. If contradiction detected, the affected peers receive a short one-paragraph acknowledgment/rebuttal prompt — not a full re-analysis. Then Synthesizer produces updated memo.
  4. Revised memo passes through Guardrail and returns to `human_review`.
- `human_feedback_history` in state stores all feedback notes and which round they were submitted in, for the record and for display in the UI timeline

### F9 — External Action

- Single integration: Slack webhook (MVP) or SendGrid email (pick one per deployment)
- Fires only after explicit human approval
- Sends the formatted memo as a message/email
- Action status stored in graph state; shown as confirmation in the UI

---

## 8. System Architecture (TRD)

### High-level components

```
Frontend (Streamlit)
    ↕ REST
FastAPI backend
    ↕
LangGraph StateGraph
    ├── ingest_context (RAG)
    ├── expert_growth / expert_finance / expert_risk (parallel fan-out)
    ├── moderator
    ├── [conditional] expert_growth_r2 / expert_finance_r2 / expert_risk_r2
    ├── [conditional] arbiter
    ├── synthesizer
    ├── guardrail_check
    ├── human_review (interrupt node)
    └── action_executor
        ↕
LangSmith (tracing)
External action (Slack/email)
```

### Component responsibilities

| Component | Responsibility |
|-----------|---------------|
| FastAPI | Accepts run requests, manages LangGraph checkpointer, exposes HITL approve/reject endpoint |
| LangGraph StateGraph | Orchestrates all agent nodes, routing, state passing, interrupt/resume |
| Chroma/FAISS | In-process vector store for RAG; single index per run, discarded after |
| LangSmith | Traces every node; shows inputs, outputs, latency, token counts |
| Streamlit | Problem input, live debate timeline view, memo review UI, HITL controls |

---

## 9. Agent Specifications

### Growth Agent

**Role:** Market opportunity, competitive landscape, growth trajectory  
**System prompt focus:** Think as a growth-oriented business analyst. Evaluate the problem from the lens of market size, competitive positioning, user/customer demand, and expansion potential. Be specific about assumptions. Flag where you lack data.  
**Tools:** web_search (Tavily/Serper), doc_retrieval  
**Output:** `ExpertAnalysis`

### Finance Agent

**Role:** Financial viability, ROI, cost structure, funding implications  
**System prompt focus:** Think as a CFO. Evaluate the problem from the lens of unit economics, cash flow impact, ROI/NPV, and financial risk. Use the financial calculator tool for quantitative estimates. Be explicit about your assumptions and discount rates.  
**Tools:** financial_calculator, doc_retrieval  
**Output:** `ExpertAnalysis`

### Risk Agent

**Role:** Operational, legal, reputational, and market risk  
**System prompt focus:** Think as a Chief Risk Officer. Evaluate the problem from the lens of what could go wrong: regulatory exposure, execution risk, reputational risk, market risk, and tail risks. Rate each risk by severity and likelihood. Be pessimistic by design — your role is to find what the others might miss.  
**Tools:** web_search (Tavily/Serper), doc_retrieval  
**Output:** `ExpertAnalysis`

### Moderator (not an LLM agent — deterministic + LLM summary)

**Role:** Disagreement detection and report generation  
**Mechanism:** Deterministic disagreement scoring (as defined in F3) + LLM call to produce a human-readable summary of the specific points of conflict  
**Output:** `DisagreementReport`

### Arbiter (LLM agent, narrow scope)

**Role:** Rules on specific disputed points only  
**System prompt focus:** You are an impartial arbiter. You will be given a list of specific disputed points between expert agents. For each point, decide which position is better supported by the evidence presented, explain your reasoning in one paragraph, and record your ruling. Do not re-analyze the full problem.  
**Tools:** none  
**Output:** `ArbitrationResult`

### Synthesizer (LLM agent)

**Role:** Produces and iteratively revises the decision memo  
**System prompt focus:** You are a strategy consultant writing a decision memo for a senior executive. Synthesize the expert analyses into a coherent memo. Where experts agreed, present the consensus. Where they disagreed and the arbiter ruled, present the ruling. Where disagreement was not resolved, present both positions clearly and label them as unresolved. Do not pretend consensus exists where it does not.  
When given a human feedback note alongside an existing memo, first attempt to resolve the feedback using the existing analyses without requesting agent revision. If the feedback requires information no agent provided or requires an agent to revisit a quantitative assumption, set `requires_agent_revision: true` and name the `target_agent`.  
**Tools:** none  
**Output:** `DecisionMemo` (initial) or `SynthesizerFeedbackDecision` (on feedback rounds)

---

## 10. Data Schemas (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from enum import Enum

class Recommendation(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CAUTION = "proceed-with-caution"
    DO_NOT_PROCEED = "do-not-proceed"

class RiskItem(BaseModel):
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    likelihood: Literal["low", "medium", "high"]
    mitigation: Optional[str] = None

class ExpertAnalysis(BaseModel):
    agent_role: Literal["growth", "finance", "risk"]
    round: Literal[1, 2, "feedback"]  # feedback = targeted re-run from HITL
    recommendation: Recommendation
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str  # 2–4 sentences
    key_assumptions: list[str]
    supporting_evidence: list[str]  # from tools/RAG
    risks: list[RiskItem]
    dissent_notes: Optional[str] = None  # round 2: what they disagree with and why
    feedback_context: Optional[str] = None  # feedback round: what human feedback triggered this

class DisagreementPoint(BaseModel):
    topic: str
    positions: dict[str, str]  # agent_role -> their position on this topic

class DisagreementReport(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    flagged_points: list[DisagreementPoint]
    summary: str  # Human-readable 2–3 sentence summary of the main conflicts
    route_decision: Literal["skip_to_synthesis", "proceed_to_turn2", "proceed_to_arbiter"]

class ArbitrationResult(BaseModel):
    rulings: list[dict]  # [{topic, sided_with, reasoning}]
    unresolved_points: list[str]  # topics where arbiter explicitly didn't rule

class SynthesizerFeedbackDecision(BaseModel):
    """Synthesizer's routing decision on a feedback round."""
    requires_agent_revision: bool
    target_agent: Optional[Literal["growth", "finance", "risk"]] = None  # only if requires_agent_revision
    revised_memo: Optional["DecisionMemo"] = None  # populated if requires_agent_revision is False
    reasoning: str  # why it can/can't resolve feedback without agent re-run

class HumanFeedbackEntry(BaseModel):
    feedback_text: str
    feedback_round: int  # 1-indexed, increments per feedback submission
    resolved_by: Literal["synthesizer_only", "targeted_agent", "abandoned"]
    target_agent_if_any: Optional[Literal["growth", "finance", "risk"]] = None
    contradiction_detected: bool = False

class DecisionMemo(BaseModel):
    executive_summary: str
    recommendation: Recommendation
    confidence: float
    expert_positions: dict[str, ExpertAnalysis]  # agent_role -> final analysis
    key_agreements: list[str]
    key_disagreements: list[str]  # preserved even if unresolved
    arbitration_summary: Optional[str]
    risk_register: list[RiskItem]
    next_steps: list[str]
    generated_at: str  # ISO timestamp
    feedback_revision_count: int = 0  # how many feedback cycles produced this memo

class GraphState(BaseModel):
    problem_statement: str
    context_docs: list[str] = []
    retriever: Optional[object] = None
    turn1_analyses: dict[str, ExpertAnalysis] = {}
    turn2_analyses: dict[str, ExpertAnalysis] = {}
    feedback_analyses: dict[str, ExpertAnalysis] = {}  # targeted re-runs from feedback rounds
    disagreement_report_t1: Optional[DisagreementReport] = None
    disagreement_report_t2: Optional[DisagreementReport] = None
    arbitration_result: Optional[ArbitrationResult] = None
    final_memo: Optional[DecisionMemo] = None
    guardrail_passed: bool = False
    human_decision: Optional[Literal["approved", "feedback", "abandoned"]] = None
    current_feedback_text: Optional[str] = None  # text of the most recent feedback note
    human_feedback_history: list[HumanFeedbackEntry] = []  # full record of all feedback rounds
    action_status: Optional[str] = None
    current_turn: int = 1
    feedback_round: int = 0  # increments on each human feedback submission
    run_id: str
```

---

## 11. LangGraph State and Graph Design

### Node list

| Node | Type | Description |
|------|------|-------------|
| `ingest_context` | Function node | Chunking, embedding, vector store creation |
| `expert_growth` | Agent node | Turn 1 Growth analysis |
| `expert_finance` | Agent node | Turn 1 Finance analysis |
| `expert_risk` | Agent node | Turn 1 Risk analysis |
| `moderator_t1` | Function + LLM | Disagreement scoring after turn 1 |
| `expert_growth_r2` | Agent node | Turn 2 Growth revision |
| `expert_finance_r2` | Agent node | Turn 2 Finance revision |
| `expert_risk_r2` | Agent node | Turn 2 Risk revision |
| `moderator_t2` | Function + LLM | Disagreement scoring after turn 2 |
| `arbiter` | Agent node | Turn 3 dispute resolution |
| `synthesizer` | Agent node | Decision memo generation |
| `guardrail_check` | Function node | Schema + policy validation |
| `human_review` | Interrupt node | Pauses for human approve/edit/reject |
| `action_executor` | Function node | Fires Slack/email if approved |

### Conditional edges

```
moderator_t1 → {
    score < 0.2:  "synthesizer",
    else:         "expert_growth_r2" (fan-out to all three)
}

moderator_t2 → {
    score < 0.7:  "synthesizer",
    else:         "arbiter"
}

human_review → {
    approved:  "action_executor",
    edited:    "action_executor",  # sends edited memo
    rejected:  END
}
```

### Parallel fan-out

Turn 1 agents run in parallel using LangGraph's `Send` API or a fan-out subgraph. Same pattern for turn 2.

### Checkpointing

SQLite-backed LangGraph checkpointer enables the graph to pause at `human_review` and resume when the human responds via the FastAPI endpoint.

---

## 12. Tool Specifications

### web_search

- Provider: Tavily API (preferred) or Serper
- Used by: Growth agent, Risk agent
- Input: natural language query string
- Output: list of `{title, url, snippet}` results, top 5
- Rate limit handling: retry once on 429, surface error in agent output if still failing

### financial_calculator

- Pure Python deterministic function (no external API)
- Inputs: `principal`, `rate`, `periods`, `cash_flows` (list)
- Outputs: `{roi, npv, irr, breakeven_period}`
- Finance agent calls this with values extracted from the problem statement or context docs
- Returns clearly labeled results with the formulas used, so the LLM output can cite them

### doc_retrieval

- LangChain retriever wrapping the Chroma/FAISS index built in `ingest_context`
- Input: query string (role-framed per agent)
- Output: top 4 chunks with source label
- Used by all three expert agents
- If no docs were uploaded, returns empty list; agents proceed on model knowledge + web search only

---

## 13. RAG Pipeline

### Ingestion (once per run, in `ingest_context` node)

1. Accept uploaded files (PDF, plain text, markdown)
2. Extract text (PyPDF2 for PDF, direct read for text/md)
3. Split into chunks: ~600 tokens, 80-token overlap (LangChain `RecursiveCharacterTextSplitter`)
4. Embed: `text-embedding-3-small` (OpenAI) or `all-MiniLM-L6-v2` (local, fallback)
5. Store in Chroma in-memory collection, tagged with source filename and chunk index

### Retrieval (per expert, at agent invocation time)

- Each agent issues a role-framed query (e.g. Finance: "financial projections ROI cost structure {problem_statement}")
- Top 8 chunks retrieved by cosine similarity (wider candidate pool for reranker)
- Cross-encoder reranker (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`) rescores the 8 candidates and returns the top 4 — higher precision than cosine similarity alone
- Reranked top 4 chunks injected into agent prompt under a `[Supporting Context]` header, clearly labeled as external evidence
- If no index exists (no docs uploaded), retrieval step is skipped gracefully

---

## 14. Guardrails and Safety

### Schema validation

- Every agent node wraps its LLM call in a validation step: parse the output against the expected Pydantic schema
- On validation failure: retry once with an explicit correction prompt ("Your output was missing the `risks` field. Please regenerate with a valid `risks` list.")
- On second failure: raise a system error, log to LangSmith, surface error to user in UI

### Policy check (on DecisionMemo before HITL)

Rule-based checks (fast, deterministic):
- `recommendation` field must be a valid enum value
- `risk_register` must not be empty
- `next_steps` must not be empty
- `executive_summary` must be at least 50 characters

LLM-based check (runs after rule-based):
- Prompt: "Review this memo. Flag it if it recommends: anything illegal, anything discriminatory, anything that could cause serious harm to a third party. Return `{passed: bool, reason: str}`."
- If flagged: memo is blocked, reason shown to user, run logged to LangSmith

### What guardrails do NOT cover

- Factual accuracy of agent analyses (not verifiable at runtime)
- Quality of external data returned by tools (logged, not blocked)

---

## 15. Human-in-the-Loop

- Implemented via LangGraph `interrupt()` at the `human_review` node
- Graph state is persisted to SQLite via checkpointer when the interrupt fires
- FastAPI exposes a `POST /runs/{run_id}/review` endpoint accepting `{decision: "approved"|"edited"|"rejected", edited_memo: str|null}`
- Frontend polls `GET /runs/{run_id}/status` for the current run state and renders the review UI when `status == "awaiting_review"`
- On resume: graph loads from checkpoint, injects the human decision into state, routes accordingly
- The external action (Slack/email) fires only after explicit approval — it is never triggered automatically

---

## 16. Evaluation Plan

Five test scenarios, each targeting a different code path:

| # | Scenario | Expected path | What it validates |
|---|----------|--------------|-------------------|
| 1 | "Should we expand into the EU market?" (with financial projections doc) | Turn 1 → Turn 2 → Synthesis | Normal full debate |
| 2 | "Should we run a 20% discount campaign this week?" (no docs) | Turn 1 → skip to Synthesis (obvious agree: proceed-with-caution) | Consensus early-exit |
| 3 | "Should we acquire a competitor at 5x revenue?" | Turn 1 → Turn 2 → Arbiter → Synthesis | Turn 3 Arbiter trigger |
| 4 | "Should we hire 10 engineers ahead of revenue?" (with burn rate doc) | Turn 1 → Turn 2 → Synthesis | RAG meaningfully changes Finance/Risk outputs |
| 5 | Adversarial: prompt injection attempt in problem statement | Guardrail blocks | Guardrail effectiveness |

For each scenario: log all node outputs, disagreement scores, route taken, memo, guardrail result. Score memo manually on: recommendation clarity (1–5), risk completeness (1–5), dissent preservation (1–5).

---

## 17. Observability

- LangSmith project created at run start, run_id passed through all nodes
- Every node wrapped in LangSmith trace: records input state, output, latency, token count, model name
- Disagreement scores logged as custom metadata on moderator traces
- Guardrail check/fail events logged as custom events
- HITL decision (approve/edit/reject) logged as a trace annotation
- Local fallback: if LangSmith is unavailable, structured JSON logs written to `logs/` directory

---

## 18. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Orchestration | LangGraph (Python) | Native support for fan-out, conditional edges, interrupt/resume |
| LLM | Claude claude-sonnet-4-6 via Anthropic API | Single model, role-differentiated prompts |
| Web search tool | Tavily API | Clean LangChain integration, reliable for demos |
| Financial calculator | Custom Python function | Deterministic, auditable, no API dependency |
| Embeddings | text-embedding-3-small (OpenAI) | Fast, cheap, good enough for demo-scale RAG |
| Vector store | Chroma (in-memory) | Zero infrastructure, in-process, sufficient for MVP |
| Schema validation | Pydantic v2 | Native LangChain/LangGraph integration |
| Checkpointing | LangGraph SQLiteCheckpointer | Enables interrupt/resume without a separate DB |
| Backend | FastAPI | Async, lightweight, good SSE support for streaming |
| Frontend | Streamlit | Fastest to build, sufficient for demo |
| Observability | LangSmith | Native LangGraph tracing |
| External action | Slack Incoming Webhook | Simple, no OAuth, easy to demo live |

---

## 19. Tradeoffs Considered

| Decision | Alternative | Why we chose this |
|----------|-------------|-------------------|
| Fixed 3-agent roster | Configurable agents | Adds prompt-engineering and eval complexity; no rubric credit |
| Capped at 3 turns | Unlimited | Prevents infinite loops; round 3 is rare by design; simpler demo |
| Deterministic disagreement score | Pure LLM judgment | More reliable triggering; easier to debug and calibrate |
| In-memory Chroma | Pinecone/Weaviate | No infrastructure; demo-scale corpus; ephemeral by design |
| Arbiter rules only on flagged points | Full third-round debate | Third repeat of same pattern adds no signal; arbiter is faster and narrower |
| Financial calculator as Python function | LLM-generated code | Predictable output; no code execution risk; easy to guardrail |
| HITL gates only final send action | HITL on every expert output | Keeps human role meaningful; shows agents operating autonomously |
| SQLite checkpointer | Redis/Postgres | Zero-infrastructure; sufficient for single-session MVP |
| LangGraph over CrewAI | CrewAI | Fan-out + conditional re-entry is natively expressible as a graph |
