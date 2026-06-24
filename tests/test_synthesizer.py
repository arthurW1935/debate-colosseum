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

@patch("src.agents.synthesiser.run_feedback_check")
def test_synthesizer_feedback_synthesizer_only(mock_feedback_check):
    # Setup mock feedback decision (synthesizer-only resolution)
    mock_revised_memo = DecisionMemo(
        executive_summary="Consensus is proceed, revised for headcount",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        expert_positions=[],
        key_agreements=["Agree"],
        key_disagreements=[],
        risk_register=[],
        next_steps=["Next steps"],
        generated_at="2026-06-23T12:00:00Z",
        feedback_revision_count=1
    )
    mock_feedback_check.return_value = SynthesizerFeedbackDecision(
        requires_agent_revision=False,
        target_agent=None,
        revised_memo=mock_revised_memo,
        reasoning="Resolved by synthesizer directly"
    )

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-2",
        final_memo=DecisionMemo(
            executive_summary="Consensus is proceed",
            recommendation=Recommendation.PROCEED,
            confidence=0.8,
            expert_positions=[],
            key_agreements=["Agree"],
            key_disagreements=[],
            risk_register=[],
            next_steps=["Next steps"],
            generated_at="2026-06-23T12:00:00Z",
            feedback_revision_count=0
        ),
        current_feedback_text="Consider headcount dependency",
        feedback_round=1
    )

    result = synthesizer(state)
    assert isinstance(result, dict)
    assert result["final_memo"].executive_summary == "Consensus is proceed, revised for headcount"
    assert result["final_memo"].feedback_revision_count == 1
    assert result["action_status"] == "resolved_by_synthesizer"
    assert len(result["human_feedback_history"]) == 1
    assert result["human_feedback_history"][0].resolved_by == "synthesizer_only"
    assert result["current_feedback_text"] is None  # Should be cleared

@patch("src.agents.synthesiser.run_feedback_check")
def test_synthesizer_feedback_targeted_agent(mock_feedback_check):
    # Setup mock feedback decision (requires agent revision)
    mock_feedback_check.return_value = SynthesizerFeedbackDecision(
        requires_agent_revision=True,
        target_agent="finance",
        revised_memo=None,
        reasoning="Finance needs to recalculate ROI"
    )

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-3",
        final_memo=DecisionMemo(
            executive_summary="Consensus is proceed",
            recommendation=Recommendation.PROCEED,
            confidence=0.8,
            expert_positions=[],
            key_agreements=["Agree"],
            key_disagreements=[],
            risk_register=[],
            next_steps=["Next steps"],
            generated_at="2026-06-23T12:00:00Z",
            feedback_revision_count=0
        ),
        current_feedback_text="Finance ROI is wrong",
        feedback_round=1
    )

    result = synthesizer(state)
    assert isinstance(result, dict)
    assert result["action_status"] == "revision_required:finance"
    assert len(result["human_feedback_history"]) == 1
    assert result["human_feedback_history"][0].resolved_by == "targeted_agent"
    assert result["human_feedback_history"][0].target_agent_if_any == "finance"
    # Bug 3 fix: current_feedback_text should NOT be cleared here —
    # the feedback agent needs it and will clear it after consuming
    assert "current_feedback_text" not in result

