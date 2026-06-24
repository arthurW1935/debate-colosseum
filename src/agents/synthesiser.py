import datetime
from src.schemas import GraphState, DecisionMemo, SynthesizerFeedbackDecision, HumanFeedbackEntry, ExpertAnalysis
from src.config import get_chat_model

SYNTHESIZER_SYSTEM_PROMPT = """You are a strategy consultant writing a structured decision memo for a senior executive.
Your task is to synthesize the expert analyses (Growth, Finance, Risk) and the Arbiter's rulings (if any) into a single, cohesive `DecisionMemo`.

Guidelines:
1. Recommendation: Provide a synthesized recommendation enum value ("proceed", "proceed-with-caution", "do-not-proceed"). If the experts agree, follow their consensus. If they disagreed and the Arbiter ruled, follow the Arbiter's ruling. If disagreements remain unresolved by the Arbiter, exercise your judgment to determine the best path based on the balance of evidence, and explain the reasoning clearly in the summary.
2. Confidence: Provide a confidence score (float 0.0 - 1.0) reflecting the overall consensus, expert confidences, and the presence of unresolved conflicts or Arbiter rulings.
3. Expert Positions: Provide a list of all final ExpertAnalysis objects in the `expert_positions` list.
4. Key Agreements: List specific points where the expert agents agreed.
5. Key Disagreements: List specific points where they disagreed. Note that any dissent that was not resolved by the Arbiter must be explicitly preserved here.
6. Arbitration Summary: If the Arbiter ran and produced rulings, summarize them here. If the Arbitration Result section says the Arbiter did not run or is empty, you MUST set `arbitration_summary` to null. Do NOT fabricate or assume arbitration outcomes.
7. Risk Register: Collect and consolidate all risks identified by the experts into a single list of `RiskItem`s. Avoid duplicates, and keep mitigations if provided.
8. Next Steps: Suggest concrete, actionable next steps based on the recommendation and risks.
9. Generated At: Use the current ISO timestamp or leave it blank for the system to populate.

Ensure you preserve dissent where appropriate and do not flatten differences in opinion unless resolved by the Arbiter."""



def get_synthesized_memo(
    problem_statement: str, 
    analyses: dict[str, ExpertAnalysis], 
    disagreement_report: str, 
    arbitration_result: str,
    feedback_revision_count: int,
    explicit_instructions: str = None
) -> DecisionMemo:
    model = get_chat_model(temperature=0.0)
    structured_model = model.with_structured_output(DecisionMemo)
    
    analyses_str = ""
    for role, analysis in analyses.items():
        analyses_str += f"### {role.upper()} AGENT ANALYSIS:\n"
        analyses_str += f"Recommendation: {analysis.recommendation.value}\n"
        analyses_str += f"Confidence: {analysis.confidence}\n"
        analyses_str += f"Summary: {analysis.summary}\n"
        analyses_str += f"Key Assumptions: {', '.join(analysis.key_assumptions)}\n"
        analyses_str += f"Supporting Evidence: {', '.join(analysis.supporting_evidence)}\n"
        analyses_str += f"Risks: {[{'desc': r.description, 'sev': r.severity, 'like': r.likelihood} for r in analysis.risks]}\n\n"
        
    user_content = (
        f"Problem Statement: {problem_statement}\n\n"
        f"Expert Analyses:\n{analyses_str}\n\n"
        f"Latest Disagreement Report:\n{disagreement_report}\n\n"
        f"Arbitration Result:\n{arbitration_result}\n"
    )
    
    if explicit_instructions:
        user_content += f"\n[EXPLICIT EDIT INSTRUCTIONS FROM MODERATOR]\n{explicit_instructions}\n"
        user_content += "\nYou MUST apply these edit instructions to the current memo and return the fully revised memo.\n"
    
    messages = [
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    
    try:
        memo = structured_model.invoke(messages)
    except Exception as e:
        memo = None

    if memo is None:
        try:
            memo = structured_model.invoke(messages)
        except Exception as e2:
            memo = None

    if memo is None:
        from src.schemas import Recommendation
        from collections import Counter
        recs = [a.recommendation for a in analyses.values()]
        most_common_rec = Counter(recs).most_common(1)[0][0] if recs else Recommendation.PROCEED_WITH_CAUTION
        
        memo = DecisionMemo(
            executive_summary="Fallback memo generated due to LLM structured parsing failure.",
            recommendation=most_common_rec,
            confidence=0.0,
            expert_positions=list(analyses.values()),
            key_agreements=["LLM failed to parse response."],
            key_disagreements=[],
            arbitration_summary="LLM failed to parse arbitration.",
            risk_register=[],
            next_steps=["Review logs for parsing errors."],
            generated_at="",
            feedback_revision_count=feedback_revision_count
        )
            
    # Set generated_at and revision count in Python to ensure correctness
    memo.generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    memo.feedback_revision_count = feedback_revision_count
    memo.expert_positions = list(analyses.values())
    
    # Sanitize arbitration_summary if arbiter did not run
    if arbitration_result.startswith("The Arbiter did not run"):
        memo.arbitration_summary = "The Arbiter did not run."
        
    return memo

def synthesizer(state: GraphState) -> dict:
    """Synthesizer node."""
    base_analyses = state.turn2_analyses if state.turn2_analyses else state.turn1_analyses
    analyses = {**base_analyses, **state.feedback_analyses}
    
    disagreement_report = ""
    if state.disagreement_report_t2:
        disagreement_report = state.disagreement_report_t2.model_dump_json(indent=2)
    elif state.disagreement_report_t1:
        disagreement_report = state.disagreement_report_t1.model_dump_json(indent=2)
        
    arbitration_result = ""
    if (state.arbitration_result
            and (state.arbitration_result.rulings or state.arbitration_result.unresolved_points)):
        arbitration_result = state.arbitration_result.model_dump_json(indent=2)
    else:
        arbitration_result = "The Arbiter did not run. Do not reference or fabricate any arbitration results."

    memo = get_synthesized_memo(
        state.problem_statement, 
        analyses, 
        disagreement_report, 
        arbitration_result,
        state.feedback_round,
        state.synthesizer_instructions
    )
    
    result = {"final_memo": memo}
    
    if state.current_feedback_text:
        feedback_entry = HumanFeedbackEntry(
            feedback_text=state.current_feedback_text,
            feedback_round=state.feedback_round,
            resolved_by="synthesizer_only" if state.synthesizer_instructions else "targeted_agent",
            target_agent_if_any=None,
            contradiction_detected=False
        )
        result["human_feedback_history"] = [feedback_entry]
        result["current_feedback_text"] = None
        result["action_status"] = "resolved_by_synthesizer"
        result["synthesizer_instructions"] = None
        
    return result

