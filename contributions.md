# Individual Contribution Report — Debate Colosseum
This document outlines the individual contributions, responsibilities, and specific implementations delivered by each of the four team members for the **Debate Colosseum** capstone project. The project was structured into four distinct development tracks (Tracks A, B, C, and D) to enable parallel execution and clean separation of concerns.
---
## Technical Architecture Overview
Debate Colosseum is a multi-agent business decision platform designed to ingest business problem statements, analyze them using domain-specific expert agents, measure disagreement, facilitate peer-aware revisions, arbitrate unresolved conflicts, and compile a structured executive decision memo. 
The division of labor was mapped as follows:
* **Track A:** Context Ingestion, Vector Indexing, and Shared Retrieval Tools
* **Track B:** Domain Expert Agents (Turn 1 and 2) and Quantitative Calculations
* **Track C:** Judgment Chain, Routing, Moderation, Arbitration, and Safety Guardrails
* **Track D:** FastAPI Backend, Checkpointing, Human-in-the-Loop Web UI, Observability, and Evaluation
---
## Track A: Ingestion & Shared Retrieval Tools
**Owner: Member A (Context & Search Engineer)**
Member A was responsible for the data ingestion pipeline and the shared tools that supply context to the expert agents. This track focused on document parsing, semantic search optimization, and web integration.
### Core Deliverables
* **Document Ingestion Pipeline (`src/rag/ingest.py`):**
  * Implemented text extraction for `.pdf`, `.txt`, and `.md` files. Integrated `PyPDF2` for handling multi-page PDF documents.
  * Configured `RecursiveCharacterTextSplitter` with a chunk size of 600 tokens and an overlap of 80 tokens.
  * Configured an ephemeral, in-memory Chroma vector store collection initialized per-run to ensure data privacy.
  * Authored the `ingest_context` LangGraph node to update the global `GraphState` with the initialized retriever.
* **Semantic Document Retrieval Tool (`src/tools/doc_retrieval.py`):**
  * Built a two-stage retrieval mechanism: retrieves the top 8 candidate chunks via cosine similarity, then reranks them to the top 4 using a local Cross-Encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`).
  * Implemented a silent fallback mode: if a user submits a problem statement without uploading documents, the retriever evaluates to `None`, and the tool returns an empty list without throwing an exception.
* **External Web Search Tool (`src/tools/web_search.py`):**
  * Wrapped the Tavily search API to fetch external market data.
  * Configured rate-limit handling to catch HTTP 429 exceptions and retry once before returning a graceful error message.
  * Enforced schema compliance, formatting search results into a clean list of `{title, url, snippet}` structures.
### Files Touched or Created
* `src/rag/ingest.py` — Raw text extraction, chunking, and Chroma collection setup.
* `src/tools/doc_retrieval.py` — Retrieval tool with local cross-encoder reranking.
* `src/tools/web_search.py` — Tavily web search tool with retry mechanics.
* `src/tools/README.md` — Integration contracts and specifications for the other tracks.
* `tests/test_rag.py` — Tests for document chunking, indexing, and rerank accuracy.
* `tests/test_tools.py` — Unit tests for the Tavily integration.
* `tests/test_ingest_node.py` — Node-level tests verifying state mutations.
---
## Track B: Domain-Specific Expert Agents
**Owner: Member B (Agent Behavior & Calculations Engineer)**
Member B focused on agent persona design, system prompt engineering, quantitative tool integration, and enabling peer-aware agent interactions during Turn 2.
### Core Deliverables
* **Expert Agent Personas (`src/agents/`):**
  * **Growth Agent (`growth.py`):** Structured prompts targeting market expansion, competitive positioning, and customer acquisition.
  * **Finance Agent (`finance.py`):** Prompts focusing on unit economics, capital allocation, and budgeting. Integrated the financial calculator.
  * **Risk Agent (`risk.py`):** Prompts designed to identify operational, legal, reputational, and compliance risks. Formatted risks as a structured list of severity and likelihood ratings.
* **Agent Execution Wrapper (`src/agents/base_wrapper.py`):**
  * Created a unified wrapper utilizing LangChain's `with_structured_output` to enforce Pydantic schema validation.
  * Implemented an auto-retry loop: on schema validation failure, the wrapper makes a second call injecting the validation error as feedback to the model.
* **Deterministic Financial Calculator (`src/tools/financial_calc.py`):**
  * Built pure Python mathematical functions to compute Return on Investment (ROI), Net Present Value (NPV), Internal Rate of Return (IRR), and breakeven periods. This provided the Finance agent with precise mathematical grounding, avoiding LLM arithmetic errors.
* **Turn 2 Peer-Aware Revision Logic:**
  * Added conditional prompt injection for `turn == 2`.
  * Extracted peers' Turn 1 recommendations, confidence scores, and summaries, alongside the moderator's conflict report, injecting them into each agent's Turn 2 context.
  * Enforced the generation of explicit `dissent_notes` whenever an agent chose to maintain a stance that disagreed with its peers.
### Files Touched or Created
* `src/agents/growth.py` — Growth agent implementation and prompt configuration.
* `src/agents/finance.py` — Finance agent implementation and quantitative integration.
* `src/agents/risk.py` — Risk agent implementation and risk-profile formatting.
* `src/agents/base_wrapper.py` — Unified agent execution and schema validation wrapper.
* `src/tools/financial_calc.py` — Mathematical formulas for ROI, NPV, IRR, and breakeven.
* `tests/test_agents_t1.py` — Isolated testing of Turn 1 agent schemas.
* `tests/test_agents_t2.py` — Verification of Turn 2 peer injection and dissent logging.
---
## Track C: Judgment Chain & Safety Guardrails
**Owner: Member C (Orchestration & Moderation Engineer)**
Member C was responsible for designing the moderation, arbitration, synthesis, and safety mechanisms. This track focused on establishing the routing thresholds and compiling the final deliverables.
### Core Deliverables
* **Moderation and Disagreement Scorer (`src/agents/moderator.py`):**
  * Developed a deterministic scoring heuristic (0.0 to 1.0) evaluating:
    * Recommendation label mismatches (proceed, caution, do not proceed).
    * Normalized standard deviation of confidence scores.
    * Divergence in risk severity ratings.
  * Implemented an LLM-based call to summarize flagged conflicts into a `DisagreementReport`.
  * Established the routing thresholds: score < 0.2 routes to the Synthesizer; score $\ge$ 0.2 routes to Turn 2; score $\ge$ 0.7 after Turn 2 routes to the Arbiter.
* **Impartial Arbiter Agent (`src/agents/arbiter.py`):**
  * Engineered an Arbiter persona that rules specifically on the conflicts listed in the `DisagreementReport`. The Arbiter is constrained to ruling on existing arguments rather than running a new debate.
* **Synthesizer Agent (`src/agents/synthesiser.py`):**
  * Designed the prompt that compiles final analyses, dissent, and arbitration rulings into a unified `DecisionMemo`.
  * Coded the human feedback routing: parses incoming human feedback to check if it can be resolved by the Synthesizer alone, or if it requires target agent revision.
* **Dual-Stage Guardrail System (`src/guardrails/checks.py`):**
  * **Stage 1 (Deterministic):** Validates memo structure, ensuring the risk register and next steps are not empty, and that the summary meets minimum length requirements.
  * **Stage 2 (LLM-based):** Executes an ethical and policy safety check to block recommendations involving illegal, discriminatory, or high-risk activities.
### Files Touched or Created
* `src/agents/moderator.py` — Disagreement calculation and routing logic.
* `src/agents/arbiter.py` — Targeted conflict arbitration node.
* `src/agents/synthesiser.py` — Decision memo compiler and feedback router.
* `src/guardrails/checks.py` — Deterministic and LLM-based safety checks.
* `tests/test_moderator.py` — Tests verifying the mathematical bounds of the scorer.
* `tests/test_synthesizer.py` — Verification of dissent preservation in the final memo.
* `tests/test_guardrails.py` — Safety test cases (passing, blocking, and incomplete states).
---
## Track D: Full Graph Assembly, API, UI & Eval
**Owner: Member D (Integration & Interface Engineer)**
Member D served as the systems integrator. Responsibilities included assembling the final LangGraph workflow, managing API endpoints, implementing state persistence, building the user interface, and establishing the evaluation harness.
### Core Deliverables
* **LangGraph Workflow Assembly (`src/graph.py`):**
  * Assembled all agent and function nodes, defining the parallel fan-outs for Turn 1 and Turn 2, conditional routing edges, and the human review interrupt point.
* **FastAPI Backend Services (`src/api/main.py`):**
  * Built the async REST API hosting `/runs` (submission with file uploads), `/runs/{id}/status` (polling for state and timeline updates), and `/runs/{id}/review` (resuming the graph with human feedback).
  * Integrated LangGraph's `MemorySaver` checkpointer for session state persistence, enabling the graph to pause at the interrupt point and resume asynchronously.
* **Human-in-the-Loop Update Mechanics (`src/hitl/review.py`):**
  * Designed the pure-function `handle_review` to process human approvals, feedback logs, and manual memo edits, updating the global state safely.
* **Streamlit Frontend Dashboard (`frontend/app.py`):**
  * Designed a multi-step user interface including document uploading, an active debate timeline rendering stage-by-stage node execution statuses, and an executive memo viewer with styled risk indicators and expert position tabs.
  * Added interactive controls for approving, providing feedback, or abandoning runs.
* **Slack Action Executor:**
  * Configured an outgoing action that formats the approved `DecisionMemo` and POSTs it to a configured Slack incoming webhook.
* **Evaluation Harness (`tests/eval/run_eval.py`):**
  * Built an automated evaluation script containing 5 hardcoded test scenarios (representing EU market expansion, discount campaigns, competitor acquisitions, early-stage hiring, and prompt injection).
  * The harness executes the graph directly, records routing decisions, and logs results to the `logs/eval_results/` directory for regression testing.
### Files Touched or Created
* `src/graph.py` — Assembled LangGraph workflow and state transitions.
* `src/api/main.py` — FastAPI application and async background task runner.
* `src/hitl/review.py` — HITL state transition logic.
* `frontend/app.py` — Streamlit dashboard and user interface.
* `src/config.py` — Global settings and LangSmith tracing setups.
* `tests/eval/run_eval.py` — Multi-scenario offline evaluation harness.
* `tests/__init__.py`, `tests/eval/__init__.py` — Test package scaffolding.



```mermaid
graph TD

%% Styling and Palettes
classDef startEnd fill:#1b5e20,color:#ffffff,stroke:#0d3010,stroke-width:2px;
classDef terminal fill:#b71c1c,color:#ffffff,stroke:#6e0e0e,stroke-width:2px;
classDef decision fill:#fff3cd,color:#5c4400,stroke:#caa400,stroke-width:2px;
classDef agent fill:#e3edff,color:#0b2a6b,stroke:#5b86d6,stroke-width:1.5px;
classDef moderator fill:#ffe3e3,color:#7a1212,stroke:#d65b5b,stroke-width:1.5px;
classDef synth fill:#e8e0ff,color:#3a1a7a,stroke:#8a6bd6,stroke-width:1.5px;
classDef guard fill:#fff0db,color:#7a4a00,stroke:#d68b1a,stroke-width:1.5px;
classDef human fill:#d6f5e3,color:#0d4d2c,stroke:#2fa86b,stroke-width:2px;
classDef process fill:#f5f5f5,color:#222222,stroke:#888888,stroke-width:1.5px;
classDef inputOutput fill:#f8f9fa,color:#222222,stroke:#6c757d,stroke-width:1.5px;
classDef hitl fill:#d6f5e3,color:#0d4d2c,stroke:#2fa86b,stroke-width:2px;

%% Elements
Start([Start Run]):::startEnd

%% Input Stage
subgraph InputStage ["1. Input & RAG Ingestion"]
    Input["Problem Statement & Docs (PDF/TXT/MD)"]:::inputOutput
    IngestNode["ingest_context (Node)"]:::process
    ChromaStore[("Ephemeral Chroma DB")]:::inputOutput
    Reranker["Cross-Encoder Reranker<br/>(ms-marco-MiniLM-L-6-v2)"]:::process
end

%% Turn 1 Expert Analysis
subgraph Turn1 ["2. Turn 1: Independent Analysis"]
    GrowthT1["expert_growth (Node)<br/>Growth Agent"]:::agent
    FinanceT1["expert_finance (Node)<br/>Finance Agent"]:::agent
    RiskT1["expert_risk (Node)<br/>Risk Agent"]:::agent

    FinCalc["financial_calculator (Tool)<br/>(NPV, ROI, IRR, Breakeven)"]:::process
    TavilySearch["web_search (Tool)<br/>(Tavily API)"]:::process
    DocRetrieval["doc_retrieval (Tool)"]:::process
end

%% Moderation Stage 1
subgraph Moderation1 ["3. Turn 1 Moderation"]
    ModeratorT1["moderator_t1 (Node)<br/>Deterministic scoring (0.0 - 1.0)"]:::moderator
    CheckT1{"Score >= 0.2?"}:::decision
end

%% Turn 2 Peer-Aware Revision
subgraph Turn2 ["4. Turn 2: Peer-Aware Revision"]
    GrowthT2["expert_growth_r2 (Node)<br/>Growth Agent (Turn 2)"]:::agent
    FinanceT2["expert_finance_r2 (Node)<br/>Finance Agent (Turn 2)"]:::agent
    RiskT2["expert_risk_r2 (Node)<br/>Risk Agent (Turn 2)"]:::agent
end

%% Moderation Stage 2
subgraph Moderation2 ["5. Turn 2 Moderation"]
    ModeratorT2["moderator_t2 (Node)<br/>Deterministic re-scoring"]:::moderator
    CheckT2{"Score >= 0.7?"}:::decision
end

%% Turn 3 Arbiter
subgraph Turn3 ["6. Turn 3: Focused Arbitration"]
    ArbiterNode["arbiter (Node)<br/>Rules on specific conflicts"]:::agent
end

%% Synthesis & Guardrails
subgraph SynthesisStage ["7. Synthesis & Quality Gate"]
    SynthesizerNode["synthesizer (Node)<br/>DecisionMemo Compiler"]:::synth
    GuardrailNode["guardrail_check (Node)<br/>Rule-based + LLM Ethical Safety"]:::guard
end

%% Human in the Loop
subgraph HITL ["8. Human-in-the-Loop Review"]
    HumanReviewNode["human_review (Node)<br/>(LangGraph Interrupt Point)"]:::human
    FastAPI["FastAPI Backend<br/>POST /review"]:::process
    Streamlit["Streamlit UI<br/>Approve / Feedback / Abandon"]:::inputOutput
    CheckDecision{"Human Decision?"}:::decision
end

%% Feedback Loop
subgraph FeedbackLoop ["9. Feedback Loop Processing"]
    SlackWebhook["Slack Webhook Action<br/>(Sends Memo on Approval)"]:::inputOutput
    GatekeeperNode["moderator_gatekeeper (Node)<br/>Check feedback scope"]:::moderator
    CheckTarget{"Target?"}:::decision

    GrowthFB["expert_growth_fb (Node)"]:::agent
    FinanceFB["expert_finance_fb (Node)"]:::agent
    RiskFB["expert_risk_fb (Node)"]:::agent
end

%% Connections
Start --> Input
Input --> IngestNode
IngestNode --> ChromaStore

%% RAG Retrieval
ChromaStore --> DocRetrieval
DocRetrieval --> Reranker

Reranker --> GrowthT1
Reranker --> FinanceT1
Reranker --> RiskT1

%% Turn 1 Tooling
GrowthT1 -.-> TavilySearch
GrowthT1 -.-> DocRetrieval

FinanceT1 -.-> FinCalc
FinanceT1 -.-> DocRetrieval

RiskT1 -.-> TavilySearch
RiskT1 -.-> DocRetrieval

%% To Moderator 1
GrowthT1 --> ModeratorT1
FinanceT1 --> ModeratorT1
RiskT1 --> ModeratorT1

ModeratorT1 --> CheckT1

%% Moderator 1 Routes
CheckT1 -- "No (Score < 0.2)" --> SynthesizerNode

CheckT1 -- "Yes (Score >= 0.2)" --> GrowthT2
CheckT1 -- "Yes (Score >= 0.2)" --> FinanceT2
CheckT1 -- "Yes (Score >= 0.2)" --> RiskT2

%% Turn 2 Peer Context Injection
GrowthT2 --> ModeratorT2
FinanceT2 --> ModeratorT2
RiskT2 --> ModeratorT2

ModeratorT2 --> CheckT2

%% Moderator 2 Routes
CheckT2 -- "No (Score < 0.7)" --> SynthesizerNode
CheckT2 -- "Yes (Score >= 0.7)" --> ArbiterNode

ArbiterNode --> SynthesizerNode

%% Post Synthesis
SynthesizerNode --> GuardrailNode
GuardrailNode --> HumanReviewNode

%% Human Interaction
HumanReviewNode <--> FastAPI
FastAPI <--> Streamlit

HumanReviewNode --> CheckDecision

%% Human Decision Routes
CheckDecision -- "approved" --> SlackWebhook
CheckDecision -- "abandoned" --> End([End Run]):::terminal

SlackWebhook --> End

CheckDecision -- "feedback" --> GatekeeperNode

%% Feedback Routes
GatekeeperNode --> CheckTarget

CheckTarget -- "synthesizer_only" --> SynthesizerNode
CheckTarget -- "growth" --> GrowthFB
CheckTarget -- "finance" --> FinanceFB
CheckTarget -- "risk" --> RiskFB

GrowthFB --> SynthesizerNode
FinanceFB --> SynthesizerNode
RiskFB --> SynthesizerNode
```