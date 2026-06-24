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
    # 1. Consensus — same recommendation, same confidence, no risks
    analyses_consensus = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
    }
    assert calculate_disagreement_score(analyses_consensus) == 0.0

    # 2. Mild disagreement — one agent differs on recommendation only
    #    rec distances: (proceed vs caution)=0.5, (proceed vs proceed)=0, (caution vs proceed)=0.5
    #    avg = 1.0/3 ≈ 0.3333;  score = 0.50 * 0.3333 = 0.1667
    analyses_mild = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.PROCEED, 0.8, [])
    }
    assert abs(calculate_disagreement_score(analyses_mild) - 0.1667) < 1e-4

    # 3. All recommendations differ, but same confidence, no risks
    #    rec distances: (proceed vs caution)=0.5, (proceed vs DNP)=1.0, (caution vs DNP)=0.5
    #    avg = 2.0/3 ≈ 0.6667;  score = 0.50 * 0.6667 ≈ 0.3333
    analyses_spread = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.8, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.8, []),
        "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.8, [])
    }
    assert abs(calculate_disagreement_score(analyses_spread) - 0.3333) < 1e-4

    # 4. Full divergence — all recs differ + confidence spread + risk severity gap
    #    rec avg = 0.6667; conf spread = 0.4; risk range = (3.0 - 0.0)/3 = 1.0
    #    score = 0.50*0.6667 + 0.30*0.4 + 0.20*1.0 = 0.3333 + 0.12 + 0.20 = 0.6533
    analyses_full = {
        "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.9, []),
        "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.7, []),
        "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.5, [
            RiskItem(description="Critical risk", severity="high", likelihood="high"),
        ])
    }
    assert abs(calculate_disagreement_score(analyses_full) - 0.6533) < 1e-4

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

    # 2. Disagreement path (score >= 0.2) — needs recs + confidence + risk divergence
    state_disagree = GraphState(
        problem_statement="Test problem",
        run_id="run-2",
        turn1_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 0.9, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.6, []),
            "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.5, [
                RiskItem(description="Severe risk", severity="critical", likelihood="high"),
            ])
        }
    )
    result_disagree = moderator_t1(state_disagree)
    assert result_disagree.disagreement_report_t1.score >= 0.2
    assert result_disagree.disagreement_report_t1.route_decision == "proceed_to_turn2"

@patch("src.agents.moderator.get_moderator_report")
def test_moderator_t2_routing(mock_report):
    mock_report.return_value = ModeratorLLMOutput(
        flagged_points=[],
        summary="Some disagreements"
    )

    # 1. Low/Medium disagreement path (score < 0.7) — mild rec difference only
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
    assert result_medium.disagreement_report_t2.score < 0.7
    assert result_medium.disagreement_report_t2.route_decision == "skip_to_synthesis"

    # 2. High disagreement path (score >= 0.7) — max rec divergence + confidence + risk severity
    state_high = GraphState(
        problem_statement="Test problem",
        run_id="run-4",
        turn2_analyses={
            "growth": create_mock_analysis("growth", Recommendation.PROCEED, 1.0, []),
            "finance": create_mock_analysis("finance", Recommendation.PROCEED_WITH_CAUTION, 0.6, [
                RiskItem(description="Financial risk", severity="critical", likelihood="high"),
            ]),
            "risk": create_mock_analysis("risk", Recommendation.DO_NOT_PROCEED, 0.4, [
                RiskItem(description="Critical risk", severity="critical", likelihood="high"),
                RiskItem(description="Another risk", severity="high", likelihood="medium"),
            ])
        }
    )
    result_high = moderator_t2(state_high)
    assert result_high.disagreement_report_t2.score >= 0.7
    assert result_high.disagreement_report_t2.route_decision == "proceed_to_arbiter"

