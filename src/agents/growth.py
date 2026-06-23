from typing import Dict, Any
import textwrap
from src.schemas import GraphState
from src.agents.base_wrapper import call_agent_with_retry
from src.tools.web_search import web_search
from src.tools.doc_retrieval import doc_retrieval
from langsmith import traceable

SYSTEM_PROMPT = textwrap.dedent("""
    ROLE: Growth analyst. Assess market size, competitive position, demand signals, and expansion upside for the stated problem.

    RECOMMENDATION CALIBRATION:
    - proceed: strong demand or market signal, competition is manageable
    - proceed-with-caution: viable but with real unknowns or a credible competitive threat
    - do-not-proceed: market too small, saturated, or demand unproven

    CONFIDENCE: 0.8-1.0 when hard data (search results, docs) backs the call. 0.5-0.79 for reasonable inference with flagged assumptions. Below 0.5 when mostly speculative.

    TOOLS, one pass each, no repeats:
    - doc_retrieval first if context docs exist. It is free and specific to this problem.
    - web_search only for current market or competitor data you cannot already reason about confidently. You MUST call `doc_retrieval` first, read the results, and ONLY THEN decide if `web_search` is needed. Skip it if doc_retrieval already answered the question or general knowledge is enough.
    - Round 2 and feedback rounds: do not call tools again unless a peer or the human raised a specific factual question your turn-1 findings cannot answer.

    ROUND BEHAVIOR:
    - Round 1: independent analysis only, no reference to other agents.
    - Round 2 (you will see peers' turn-1 analyses and a disagreement report): hold or revise your recommendation. If you disagree with a peer, populate `dissent_notes` using the strict format `[Peer Role]: [Specific disagreement]`. If you revise, say what changed your mind.
    - Feedback round (you will see a human note): address it directly, explain the change in feedback_context in one to two sentences. Do not restate your full prior analysis.

    OUTPUT DISCIPLINE: summary in 2-4 sentences. key_assumptions and supporting_evidence as short single-line bullets, 2-5 each. List only growth-specific risks (market or demand risk); leave operational, financial, and legal risk to the other agents. State plainly when you lack data instead of guessing.
""").strip()


@traceable(name="expert_growth")
def expert_growth(state: GraphState) -> Dict[str, Any]:
    tools = [web_search, doc_retrieval]

    analysis = call_agent_with_retry(
        state=state,
        role="growth",
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        turn=state.current_turn
    )

    if state.action_status and state.action_status.startswith("revision_required:"):
        return {"feedback_analyses": {"growth": analysis}}
    elif state.current_turn == 1:
        return {"turn1_analyses": {"growth": analysis}}
    else:
        return {"turn2_analyses": {"growth": analysis}}