# INSTRUCTIONS.md

> Working conventions for Debate Colosseum.  
> Read this before writing any code, making any PR, or asking a teammate for a review.  
> Treat this file the way a codebase treats `CLAUDE.md` — it describes how work gets done here.

---

## Project orientation

You are building a multi-agent AI system, not a web app with some LLM calls in it. The agents are first-class citizens. Before touching any file, be clear on which agent or node you are working on and what schema it consumes and produces. The schemas in `src/schemas.py` are the contract between all four of you.

If you want to change a schema, bring it to the group. Do not silently change `ExpertAnalysis` because it broke your tests — you will break B and C's code at the same time.

---

## Repo rules

### Branching

- `main` must always run. Nothing broken, no WIP commits.
- Branch naming: `{person-letter}/{short-description}` — e.g. `a/rag-pipeline`, `c/moderator-scoring`
- One feature per branch. Don't stack multiple features on the same branch.
- Merge to `main` via PR only. Get at least one teammate to skim it.

### Commit messages

Follow the format from `plan.md` exactly:

```
<type>: <short description>
```

Types:
- `feat` — new functionality
- `test` — new or updated tests
- `fix` — bug fix
- `refactor` — internal change with no behavior change
- `docs` — documentation only
- `chore` — config, dependencies, scaffolding

Examples:
- `feat: growth agent turn 2 peer context injection`
- `fix: moderator score overflows 1.0 on all-disagree case`
- `test: eval scenario 3 arbiter trigger`

Do not commit with messages like `update`, `wip`, `fix stuff`, or `asdfgh`. If you can't describe what the commit does in one line, the commit is too big.

### What not to commit

- `.env` files with real API keys — use `.env.example` for structure
- Large test PDFs — use the small fixtures in `tests/fixtures/`
- LangSmith trace IDs hardcoded anywhere

---

## Code conventions

### Python style

- Python 3.11+
- Type hints on all function signatures
- Pydantic v2 for all data models
- `ruff` for linting (run `ruff check src/` before committing)
- No `print()` for debug output — use `logging` or LangSmith traces

### Agent nodes

Every LangGraph node function follows this signature:

```python
def node_name(state: GraphState) -> GraphState:
    ...
    return state
```

Nodes must:
- Read only what they need from `state`
- Return a new or updated `state` (do not mutate in place)
- Validate their output against the relevant schema before returning
- Raise `ValueError` (not silently continue) if schema validation fails after retry

### Schema changes

1. Open an issue or message the group
2. Update `src/schemas.py`
3. Update `tests/fixtures/` with a valid new fixture
4. All affected nodes must be updated in the same PR — no partial migrations

### Tools

- Tools live in `src/tools/` as standalone functions — they are not methods on agent classes
- Tools must have their own tests in `tests/test_tools.py`
- Tools return structured data (dict or list of dicts), never raw strings
- If a tool fails, raise a descriptive exception — the calling agent handles the retry or fallback, not the tool itself

### Agents

- Agent system prompts live in the agent file, not in a separate prompt file (for now)
- Every agent call is wrapped in a try/except that catches validation failure and retries once
- Agent files import tools — tools do not import agents (no circular deps)

---

## Environment setup

```bash
# Clone and set up
git clone https://github.com/your-org/debate-colosseum
cd debate-colosseum
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy and fill env vars
cp .env.example .env
# Edit .env with your keys (see below)

# Run tests
pytest tests/

# Run the app locally
uvicorn src.api.main:app --reload   # backend on :8000
streamlit run frontend/app.py       # frontend on :8501
```

### Required env vars (`.env`)

```
ANTHROPIC_API_KEY=          # Claude API — all agents
TAVILY_API_KEY=             # web search tool
LANGSMITH_API_KEY=          # tracing
LANGSMITH_PROJECT=debate-colosseum
SLACK_WEBHOOK_URL=          # HITL external action
```

Optional:
```
OPENAI_API_KEY=             # if using OpenAI embeddings for RAG
LOG_LEVEL=INFO
```

---

## Testing conventions

### What to test

- Every tool: unit test with real API call (use pytest-vcr or just run live for MVP)
- Every agent: test with fixture inputs → assert output validates against schema
- Moderator: test all three routing paths (score < 0.2, 0.2–0.7, ≥ 0.7)
- Guardrails: test passing memo, blocked memo, incomplete memo
- HITL: test approve and reject paths via FastAPI TestClient

### What not to test

- LLM output quality (you can't assert on prose — that's what manual eval is for)
- LangSmith trace structure

### Running eval scenarios

```bash
python tests/eval/run_eval.py --scenario all
python tests/eval/run_eval.py --scenario 3   # run single scenario
```

Output: a JSON file per scenario in `logs/eval_results/` with node outputs, scores, and routing path.

---

## LangSmith conventions

- Every run gets a `run_id` (UUID), generated at the start and stored in `GraphState`
- The LangSmith project name is always `debate-colosseum` — set in `config.py`
- When debugging a failing scenario: paste the LangSmith run URL in your PR or Slack message, not a wall of logs
- Trace names: use the node name as the trace name (`expert_growth`, `moderator_t1`, etc.)

---

## Integration day (Day 4) protocol

1. Everyone merges their feature branches to `main` in this order: A → B → C → D
2. Run `pytest tests/` after each merge. Fix before moving to next.
3. Person C leads wiring `src/graph.py` — others are available but Person C drives
4. Run scenario 1 end-to-end first. If it passes, run all 5.
5. Do not start polishing the UI until all 5 eval scenarios pass.

---

## Demo prep checklist

- [ ] All 5 eval scenarios produce valid output end-to-end
- [ ] Streamlit UI loads without error on a fresh browser
- [ ] HITL approve triggers Slack message (test live before demo)
- [ ] HITL reject saves edits and does nothing else (test this too)
- [ ] LangSmith traces visible for at least 3 scenarios
- [ ] Each person can explain their component in 90 seconds with no notes
- [ ] Individual contribution doc written and submitted

---

## Individual contribution docs

Due before evaluation. Each person writes a short doc (500–800 words) covering:

1. Which nodes/components you owned
2. Key technical decisions you made and why
3. What was harder than expected and how you solved it
4. How your component connects to the components around it
5. What you would do differently if you had more time

Submit as `contributions/{your-name}.md` in the repo, and also paste into the Google Form.

---

## If you're stuck

1. Check `PRD_TRD.md` — the thing you're implementing is probably specified there
2. Check `plan.md` — make sure you're working the right commit, in the right order
3. Check if the schema in `src/schemas.py` is what you think it is
4. Ask the group in Slack/WhatsApp before spending more than 30 minutes blocked
5. If it's an LLM output quality issue: share the prompt + a few example outputs in the group chat, not just "it's not working"
