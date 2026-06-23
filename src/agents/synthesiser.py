import datetime
from src.schemas import GraphState, DecisionMemo, SynthesizerFeedbackDecision, HumanFeedbackEntry, ExpertAnalysis
from src.config import get_chat_model

SYNTHESIZER_SYSTEM_PROMPT = """You are a strategy consultant writing a structured decision memo for a senior executive.
Your task is to synthesize the expert analyses (Growth, Finance, Risk) and the Arbiter's rulings (if any) into a single, cohesive `DecisionMemo`.

Guidelines:
1. Recommendation: Provide a synthesized recommendation enum value ("proceed", "proceed-with-caution", "do-not-proceed"). If the experts agree, follow their consensus. If they disagreed and the Arbiter ruled, follow the Arbiter's ruling. If disagreements remain unresolved by the Arbiter, exercise your judgment to determine the best path based on the balance of evidence, and explain the reasoning clearly in the summary.
2. Confidence: Provide a confidence score (float 0.0 - 1.0) reflecting the overall consensus, expert confidences, and the presence of unresolved conflicts or Arbiter rulings.
3. Expert Positions: Map each agent role to its final ExpertAnalysis object in the `expert_positions` dictionary.
4. Key Agreements: List specific points where the expert agents agreed.
5. Key Disagreements: List specific points where they disagreed. Note that any dissent that was not resolved by the Arbiter must be explicitly preserved here.
6. Arbitration Summary: Summarize the Arbiter's rulings and what was resolved, or leave it null/empty if the Arbiter did not run.
7. Risk Register: Collect and consolidate all risks identified by the experts into a single list of `RiskItem`s. Avoid duplicates, and keep mitigations if provided.
8. Next Steps: Suggest concrete, actionable next steps based on the recommendation and risks.
9. Generated At: Use the current ISO timestamp or leave it blank for the system to populate.

Ensure you preserve dissent where appropriate and do not flatten differences in opinion unless resolved by the Arbiter."""

SYNTHESIZER_FEEDBACK_CHECK_PROMPT = """You are a strategy consultant reviewing a decision memo alongside new feedback from a human reviewer.
Your task is to determine whether this feedback can be resolved solely by revising the memo (e.g. framing, tone, summary changes, or incorporating details that are already present in the existing expert analyses) OR if it requires a specific expert agent to re-run and revise their analysis (e.g. they need to look up new external data, redo a calculation, or reconsider a core assumption).

You will be given:
1. The current `DecisionMemo` (including all expert positions).
2. The new human feedback text.

You must output a `SynthesizerFeedbackDecision` object:
1. `requires_agent_revision`: Set to `True` if you need a specific expert agent (growth, finance, or risk) to revise/re-run their analysis. Set to `False` if the feedback can be resolved by updating the memo directly using existing information.
2. `target_agent`: If `requires_agent_revision` is `True`, name the target agent role ("growth", "finance", "risk"). Otherwise, set to null.
3. `revised_memo`: If `requires_agent_revision` is `False`, you must output the fully revised `DecisionMemo` incorporating the human feedback. Otherwise, set to null.
4. `reasoning`: A brief explanation of your decision (e.g. why an agent revision is needed, or how the feedback was resolved in the memo)."""

def get_synthesized_memo(
    problem_statement: str, 
    analyses: dict[str, ExpertAnalysis], 
    disagreement_report: str, 
    arbitration_result: str,
    feedback_revision_count: int
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
    
    messages = [
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    
    try:
        memo = structured_model.invoke(messages)
    except Exception as e:
        try:
            memo = structured_model.invoke(messages)
        except Exception as e2:
            raise ValueError(f"Synthesizer initial memo LLM call failed validation after retry: {e2}") from e2
            
    # Set generated_at and revision count in Python to ensure correctness
    memo.generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    memo.feedback_revision_count = feedback_revision_count
    memo.expert_positions = analyses
    return memo

def run_feedback_check(current_memo: DecisionMemo, feedback_text: str) -> SynthesizerFeedbackDecision:
    model = get_chat_model(temperature=0.0)
    structured_model = model.with_structured_output(SynthesizerFeedbackDecision)
    
    messages = [
        {"role": "system", "content": SYNTHESIZER_FEEDBACK_CHECK_PROMPT},
        {"role": "user", "content": f"Current Memo:\n{current_memo.model_dump_json(indent=2)}\n\nHuman Feedback: {feedback_text}"}
    ]
    
    try:
        decision = structured_model.invoke(messages)
    except Exception as e:
        try:
            decision = structured_model.invoke(messages)
        except Exception as e2:
            raise ValueError(f"Synthesizer feedback check LLM call failed validation after retry: {e2}") from e2
            
    return decision

def synthesizer(state: GraphState) -> GraphState:
    """Synthesizer node.
    Synthesizes the final memo, or handles human feedback rounds."""
    # Assemble the final set of analyses (override turn 2 analyses with feedback analyses)
    base_analyses = state.turn2_analyses if state.turn2_analyses else state.turn1_analyses
    analyses = {**base_analyses, **state.feedback_analyses}
    
    disagreement_report = ""
    if state.disagreement_report_t2:
        disagreement_report = state.disagreement_report_t2.model_dump_json(indent=2)
    elif state.disagreement_report_t1:
        disagreement_report = state.disagreement_report_t1.model_dump_json(indent=2)
        
    arbitration_result = ""
    if state.arbitration_result:
        arbitration_result = state.arbitration_result.model_dump_json(indent=2)
        
    # Check if we are handling a new feedback note from human
    if state.current_feedback_text:
        current_memo = state.final_memo
        if not current_memo:
            # Fallback if final_memo is missing (should not happen in normal flows)
            current_memo = get_synthesized_memo(
                state.problem_statement, 
                analyses, 
                disagreement_report, 
                arbitration_result,
                state.feedback_round
            )
            
        decision = run_feedback_check(current_memo, state.current_feedback_text)
        
        if decision.requires_agent_revision:
            # Requires targeted agent re-run
            target_agent = decision.target_agent
            if target_agent not in ["growth", "finance", "risk"]:
                # Default to finance if target agent is invalid/missing
                target_agent = "finance"
                
            feedback_entry = HumanFeedbackEntry(
                feedback_text=state.current_feedback_text,
                feedback_round=state.feedback_round,
                resolved_by="targeted_agent",
                target_agent_if_any=target_agent,
                contradiction_detected=False
            )
            
            # Clear current_feedback_text so we don't repeat the check, and set target agent in action_status
            new_state = state.model_copy(update={
                "human_feedback_history": state.human_feedback_history + [feedback_entry],
                "action_status": f"revision_required:{target_agent}",
                "current_feedback_text": None
            })
            return new_state
        else:
            # Resolved directly by the Synthesizer
            revised_memo = decision.revised_memo
            if not revised_memo:
                # Fallback if LLM failed to provide the revised memo
                revised_memo = current_memo
                
            revised_memo.generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            revised_memo.feedback_revision_count = current_memo.feedback_revision_count + 1
            revised_memo.expert_positions = analyses
            
            feedback_entry = HumanFeedbackEntry(
                feedback_text=state.current_feedback_text,
                feedback_round=state.feedback_round,
                resolved_by="synthesizer_only",
                target_agent_if_any=None,
                contradiction_detected=False
            )
            
            new_state = state.model_copy(update={
                "final_memo": revised_memo,
                "human_feedback_history": state.human_feedback_history + [feedback_entry],
                "action_status": "resolved_by_synthesizer",
                "current_feedback_text": None
            })
            return new_state
            
    # Non-feedback round or post-agent-revision round (where current_feedback_text is already processed/cleared)
    memo = get_synthesized_memo(
        state.problem_statement, 
        analyses, 
        disagreement_report, 
        arbitration_result,
        state.feedback_round
    )
    
    new_state = state.model_copy(update={
        "final_memo": memo
    })
    return new_state
