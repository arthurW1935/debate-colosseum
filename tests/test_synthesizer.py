from unittest.mock import patch, MagicMock
from src.schemas import GraphState, ExpertAnalysis, Recommendation, DecisionMemo, SynthesizerFeedbackDecision, HumanFeedbackEntry
from src.agents.synthesiser import synthesizer

def create_mock_analysis(role: str, recommendation: Recommendation, confidence: float) -> ExpertAnalysis:
    return ExpertAnalysis(
        agent_role=role,
        round="1",
        recommendation=recommendation,
        confidence=confidence,
        summary=f"Analysis by {role}",
        key_assumptions=["A"],
        supporting_evidence=["E"],
        risks=[]
    )

@patch("src.agents.synthesiser.get_synthesized_memo")
def test_synthesizer_initial_memo(mock_get_memo):
    # Setup mock synthesized memo
    mock_memo = DecisionMemo(
        executive_summary="Consensus is proceed",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        expert_positions=[],
        key_agreements=["Agree on market expansion"],
        key_disagreements=[],
        risk_register=[],
        next_steps=["Go to next phase"],
        generated_at="2026-06-23T12:00:00Z",
        feedback_revision_count=0
    )
    mock_get_memo.return_value = mock_memo

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-1",
        turn2_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED, 0.8),
            "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8)
        }
    )

    result = synthesizer(state)
    assert isinstance(result, dict)
    assert result["final_memo"].executive_summary == "Consensus is proceed"
    assert result["final_memo"].feedback_revision_count == 0

@patch("src.agents.synthesiser.get_synthesized_memo")
def test_synthesizer_with_instructions(mock_get_memo):
    mock_memo = DecisionMemo(
        executive_summary="Revised summary",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        expert_positions=[],
        key_agreements=[],
        key_disagreements=[],
        risk_register=[],
        next_steps=[],
        generated_at="2026-06-23T12:00:00Z",
        feedback_revision_count=1
    )
    mock_get_memo.return_value = mock_memo

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-4",
        turn2_analyses={},
        synthesizer_instructions="Make it shorter",
        current_feedback_text="Too long",
        feedback_round=1
    )

    result = synthesizer(state)
    assert result["final_memo"].executive_summary == "Revised summary"
    assert result["action_status"] == "resolved_by_synthesizer"
    assert result["synthesizer_instructions"] is None
    assert len(result["human_feedback_history"]) == 1
    assert result["human_feedback_history"][0].resolved_by == "synthesizer_only"

