from unittest.mock import patch
from src.schemas import GraphState, DecisionMemo, Recommendation, RiskItem
from src.guardrails.checks import guardrail_check, GuardrailSafetyDecision

def create_valid_memo() -> DecisionMemo:
    return DecisionMemo(
        executive_summary="This is a very long executive summary that exceeds the fifty characters minimum requirement.",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        expert_positions={},
        key_agreements=["Agreement A"],
        key_disagreements=[],
        risk_register=[
            RiskItem(description="Risk A", severity="low", likelihood="low", mitigation="Mitigation A")
        ],
        next_steps=["Step A"],
        generated_at="2026-06-23T12:00:00Z"
    )

@patch("src.guardrails.checks.run_llm_safety_check")
def test_guardrails_passing_memo(mock_safety_check):
    # Setup passing safety check
    mock_safety_check.return_value = GuardrailSafetyDecision(passed=True, reason="")

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-1",
        final_memo=create_valid_memo()
    )

    result = guardrail_check(state)
    assert result.guardrail_passed is True
    assert "passed" in result.action_status.lower()

def test_guardrails_incomplete_memo_rule_failures():
    # 1. Empty risk register
    memo_no_risks = create_valid_memo()
    memo_no_risks.risk_register = []
    
    state_no_risks = GraphState(
        problem_statement="Test problem",
        run_id="run-2",
        final_memo=memo_no_risks
    )
    result_no_risks = guardrail_check(state_no_risks)
    assert result_no_risks.guardrail_passed is False
    assert "risk register is empty" in result_no_risks.action_status.lower()

    # 2. Short executive summary
    memo_short_summary = create_valid_memo()
    memo_short_summary.executive_summary = "Too short."
    
    state_short = GraphState(
        problem_statement="Test problem",
        run_id="run-3",
        final_memo=memo_short_summary
    )
    result_short = guardrail_check(state_short)
    assert result_short.guardrail_passed is False
    assert "executive summary is incomplete" in result_short.action_status.lower()

    # 3. Empty next steps
    memo_no_steps = create_valid_memo()
    memo_no_steps.next_steps = []
    
    state_no_steps = GraphState(
        problem_statement="Test problem",
        run_id="run-4",
        final_memo=memo_no_steps
    )
    result_no_steps = guardrail_check(state_no_steps)
    assert result_no_steps.guardrail_passed is False
    assert "next steps section is empty" in result_no_steps.action_status.lower()

@patch("src.guardrails.checks.run_llm_safety_check")
def test_guardrails_blocked_memo(mock_safety_check):
    # Setup failing safety check (e.g. recommending something illegal)
    mock_safety_check.return_value = GuardrailSafetyDecision(
        passed=False, 
        reason="Memo recommends illegal growth hacks."
    )

    state = GraphState(
        problem_statement="Test problem",
        run_id="run-5",
        final_memo=create_valid_memo()
    )

    result = guardrail_check(state)
    assert result.guardrail_passed is False
    assert "illegal growth hacks" in result.action_status
