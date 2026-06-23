from unittest.mock import patch, MagicMock
from src.schemas import GraphState, ExpertAnalysis, Recommendation, RiskItem
from src.agents.moderator import calculate_disagreement_score, moderator_t1, moderator_t2, ModeratorLLMOutput

def create_mock_analysis(role: str, recommendation: Recommendation, confidence: float, risks: list[RiskItem]) -> ExpertAnalysis:
    return ExpertAnalysis(
        agent_role=role,
        round="1",
        recommendation=recommendation,
        confidence=confidence,
        summary="Test summary",
        key_assumptions=["A"],
        supporting_evidence=["E"],
        risks=risks
    )

def test_calculate_disagreement_score():
    # 1. Consensus
    analyses_consensus = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
    }
    assert calculate_disagreement_score(analyses_consensus) == 0.0

    # 2. Medium Disagreement (2 recommendations differ)
    analyses_medium = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
    }
    # Mismatch: Growth vs Finance (+0.3), Growth vs Risk (0), Finance vs Risk (+0.3) = 0.6
    assert abs(calculate_disagreement_score(analyses_medium) - 0.6) < 1e-5

    # 3. High Disagreement (All recommendations differ)
    analyses_high = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.8, [])
    }
    # Mismatch: Growth vs Finance (+0.3), Growth vs Risk (+0.3), Finance vs Risk (+0.3) = 0.9
    assert abs(calculate_disagreement_score(analyses_high) - 0.9) < 1e-5

@patch("src.agents.moderator.get_moderator_report")
def test_moderator_t1_routing(mock_report):
    # Setup mock LLM report
    mock_report.return_value = ModeratorLLMOutput(
        flagged_points=[],
        summary="No disagreement"
    )

    # 1. Consensus path (score < 0.2)
    state = GraphState(
        problem_statement="Test problem",
        run_id="run-1",
        turn1_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED, 0.8, []),
            "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
        }
    )
    result = moderator_t1(state)
    assert result.disagreement_report_t1.score == 0.0
    assert result.disagreement_report_t1.route_decision == "skip_to_synthesis"

    # 2. Medium/High disagreement path (score >= 0.2)
    state_disagree = GraphState(
        problem_statement="Test problem",
        run_id="run-2",
        turn1_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
            "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
        }
    )
    result_disagree = moderator_t1(state_disagree)
    assert result_disagree.disagreement_report_t1.score == 0.6
    assert result_disagree.disagreement_report_t1.route_decision == "proceed_to_turn2"

@patch("src.agents.moderator.get_moderator_report")
def test_moderator_t2_routing(mock_report):
    mock_report.return_value = ModeratorLLMOutput(
        flagged_points=[],
        summary="Some disagreements"
    )

    # 1. Low/Medium disagreement path (score < 0.7)
    state_medium = GraphState(
        problem_statement="Test problem",
        run_id="run-3",
        turn2_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
            "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
        }
    )
    result_medium = moderator_t2(state_medium)
    assert result_medium.disagreement_report_t2.score == 0.6
    assert result_medium.disagreement_report_t2.route_decision == "skip_to_synthesis"

    # 2. High disagreement path (score >= 0.7)
    state_high = GraphState(
        problem_statement="Test problem",
        run_id="run-4",
        turn2_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
            "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.8, [])
        }
    )
    result_high = moderator_t2(state_high)
    assert result_high.disagreement_report_t2.score == 0.9
    assert result_high.disagreement_report_t2.route_decision == "proceed_to_arbiter"
