from src.schemas import GraphState, ArbitrationResult
from src.config import get_chat_model

ARBITER_SYSTEM_PROMPT = """You are the impartial Arbiter in the Debate Colosseum.
Your role is to rule on specific disputed points between expert agents (Growth, Finance, Risk).

You will be given:
1. The original business problem statement.
2. The final analyses from each expert agent.
3. A disagreement report identifying the specific flagged points of disagreement.

For each flagged point of disagreement, your job is to:
1. Decide which position is better supported by the evidence and reasoning presented.
2. Write a clear, objective ruling explaining your decision in one paragraph.
3. Record the ruling in `rulings` as an object with the following keys:
   - `topic`: The name of the disputed topic.
   - `sided_with`: The agent role whose position you sided with (e.g. "finance", "growth", "risk"), or "compromise" if you created a middle-ground solution.
   - `reasoning`: A one-paragraph explanation of your ruling.
4. If a point is too close to call, lacks sufficient evidence, or cannot be resolved, add the topic name to the `unresolved_points` list.

Do not re-analyze the entire problem statement or introduce completely new topics. Only rule on the specific flagged points provided."""

def arbiter(state: GraphState) -> GraphState:
    """Arbiter agent node.
    Rules on specific disputed points and returns an ArbitrationResult.
    Always runs an LLM call when invoked — the routing decision already
    guarantees that disagreement is high enough to warrant arbitration."""
    report = state.disagreement_report_t2 or state.disagreement_report_t1
    analyses = state.turn2_analyses if state.turn2_analyses else state.turn1_analyses

    if not analyses or len(analyses) < 2:
        # Genuinely nothing to arbitrate (no expert data)
        return state.model_copy(update={
            "arbitration_result": ArbitrationResult(rulings=[], unresolved_points=[])
        })

    # Format the agent analyses for the arbiter
    analyses_str = ""
    for role, analysis in analyses.items():
        analyses_str += f"### {role.upper()} AGENT ANALYSIS:\n"
        analyses_str += f"Recommendation: {analysis.recommendation.value}\n"
        analyses_str += f"Confidence: {analysis.confidence}\n"
        analyses_str += f"Summary: {analysis.summary}\n"
        analyses_str += f"Key Assumptions: {', '.join(analysis.key_assumptions)}\n"
        analyses_str += f"Supporting Evidence: {', '.join(analysis.supporting_evidence)}\n\n"

    # Format disagreement info — use moderator's flagged points if available,
    # otherwise instruct the LLM to identify disagreements from the raw analyses.
    if report and report.flagged_points:
        disagreements_str = "Flagged Disagreements:\n"
        for pt in report.flagged_points:
            disagreements_str += f"- Topic: {pt.topic}\n"
            for pos in pt.positions:
                disagreements_str += f"  * {pos.agent_role}: {pos.stance}\n"
    else:
        disagreements_str = (
            "The Moderator did not flag specific disagreement points, but the "
            "quantitative disagreement score is high enough to warrant arbitration. "
            "Identify the key points of disagreement from the expert analyses above "
            "and rule on each one."
        )

    messages = [
        {"role": "system", "content": ARBITER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Problem Statement: {state.problem_statement}\n\nExpert Analyses:\n{analyses_str}\n\n{disagreements_str}"}
    ]

    model = get_chat_model(temperature=0.0)
    structured_model = model.with_structured_output(ArbitrationResult)

    try:
        result = structured_model.invoke(messages)
    except Exception as e:
        # Retry once
        try:
            result = structured_model.invoke(messages)
        except Exception as e2:
            raise ValueError(f"Arbiter LLM call failed validation after retry: {e2}") from e2

    new_state = state.model_copy(update={
        "arbitration_result": result
    })
    return new_state
