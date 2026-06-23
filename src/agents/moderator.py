from pydantic import BaseModel, Field
from src.schemas import GraphState, DisagreementReport, DisagreementPoint, ExpertAnalysis
from src.config import get_chat_model

class ModeratorLLMOutput(BaseModel):
    flagged_points: list[DisagreementPoint] = Field(default_factory=list)
    summary: str

MODERATOR_SYSTEM_PROMPT = """You are the Moderator in the Debate Colosseum.
Your job is to read the independent analyses of the Growth, Finance, and Risk expert agents and identify specific points of disagreement between them.

For each point of disagreement:
1. Identify a clear, concise topic (e.g., "Market size assumptions", "NPV calculation", "Regulatory risk level").
2. Detail the exact position of each agent on this topic in the `positions` dictionary mapping the agent's role (growth, finance, or risk) to their stance. Only include agents that actually expressed a position on this topic.

Finally, write a human-readable 2-3 sentence summary of the main conflicts.

Be precise, objective, and fair. Do not try to resolve the disagreements yourself; just flag where they exist.
If the agents are in complete agreement, leave `flagged_points` empty and state that there is consensus in the summary."""

def pop_std(vals: list[float]) -> float:
    if not vals:
        return 0.0
    mean = sum(vals) / len(vals)
    variance = sum((v - mean) ** 2 for v in vals) / len(vals)
    return variance ** 0.5

def calculate_disagreement_score(analyses: dict[str, ExpertAnalysis]) -> float:
    agents = ["growth", "finance", "risk"]
    present_analyses = [analyses[a] for a in agents if a in analyses]
    if len(present_analyses) < 2:
        return 0.0
        
    # 1. Recommendation mismatch
    mismatch_score = 0.0
    pairs = [("growth", "finance"), ("growth", "risk"), ("finance", "risk")]
    for a1, a2 in pairs:
        if a1 in analyses and a2 in analyses:
            if analyses[a1].recommendation != analyses[a2].recommendation:
                mismatch_score += 0.3
                
    # 2. Confidence variance (std dev)
    confidences = [analyses[a].confidence for a in agents if a in analyses]
    confidence_std = pop_std(confidences)
    
    # 3. Risk severity divergence
    severity_map = {"low": 1.0, "medium": 2.0, "high": 3.0, "critical": 4.0}
    avg_severities = []
    for a in agents:
        if a in analyses:
            risks = analyses[a].risks
            if risks:
                avg_sev = sum(severity_map.get(r.severity, 1.0) for r in risks) / len(risks)
            else:
                avg_sev = 0.0
            avg_severities.append(avg_sev)
    risk_std = pop_std(avg_severities)
    
    score = mismatch_score + confidence_std + risk_std
    return round(min(max(score, 0.0), 1.0), 4)

def get_moderator_report(problem_statement: str, analyses: dict[str, ExpertAnalysis]) -> ModeratorLLMOutput:
    model = get_chat_model(temperature=0.0)
    structured_model = model.with_structured_output(ModeratorLLMOutput)
    
    analyses_str = ""
    for role, analysis in analyses.items():
        analyses_str += f"### {role.upper()} AGENT ANALYSIS:\n"
        analyses_str += f"Recommendation: {analysis.recommendation.value}\n"
        analyses_str += f"Confidence: {analysis.confidence}\n"
        analyses_str += f"Summary: {analysis.summary}\n"
        analyses_str += f"Key Assumptions: {', '.join(analysis.key_assumptions)}\n"
        analyses_str += f"Supporting Evidence: {', '.join(analysis.supporting_evidence)}\n"
        analyses_str += f"Risks: {[{'desc': r.description, 'sev': r.severity, 'like': r.likelihood} for r in analysis.risks]}\n\n"
        
    messages = [
        {"role": "system", "content": MODERATOR_SYSTEM_PROMPT},
        {"role": "user", "content": f"Problem Statement: {problem_statement}\n\nExpert Analyses:\n{analyses_str}"}
    ]
    
    try:
        return structured_model.invoke(messages)
    except Exception as e:
        # Retry once
        try:
            return structured_model.invoke(messages)
        except Exception as e2:
            raise ValueError(f"Moderator LLM call failed validation after retry: {e2}") from e2

def moderator_t1(state: GraphState) -> GraphState:
    """Moderator node after Turn 1.
    Computes disagreement score and routes either to synthesis (consensus) or to Turn 2."""
    analyses = state.turn1_analyses
    score = calculate_disagreement_score(analyses)
    
    llm_output = get_moderator_report(state.problem_statement, analyses)
    
    route_decision = "skip_to_synthesis" if score < 0.2 else "proceed_to_turn2"
    
    report = DisagreementReport(
        score=score,
        flagged_points=llm_output.flagged_points,
        summary=llm_output.summary,
        route_decision=route_decision
    )
    
    # Return a new state to avoid mutation in place
    new_state = state.model_copy(update={
        "disagreement_report_t1": report,
        "current_turn": 1
    })
    return new_state

def moderator_t2(state: GraphState) -> GraphState:
    """Moderator node after Turn 2.
    Computes disagreement score and routes either to synthesis or to Arbiter."""
    analyses = state.turn2_analyses
    score = calculate_disagreement_score(analyses)
    
    llm_output = get_moderator_report(state.problem_statement, analyses)
    
    route_decision = "proceed_to_arbiter" if score >= 0.7 else "skip_to_synthesis"
    
    report = DisagreementReport(
        score=score,
        flagged_points=llm_output.flagged_points,
        summary=llm_output.summary,
        route_decision=route_decision
    )
    
    new_state = state.model_copy(update={
        "disagreement_report_t2": report,
        "current_turn": 2
    })
    return new_state
