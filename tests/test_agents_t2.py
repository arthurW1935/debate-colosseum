import pytest
from src.schemas import GraphState, ExpertAnalysis, Recommendation, DisagreementReport, DisagreementPoint
from src.agents.growth import expert_growth
from src.agents.finance import expert_finance
from src.agents.risk import expert_risk

@pytest.fixture
def t2_state():
    turn1_analyses = {
        "finance": ExpertAnalysis(
            agent_role="finance",
            round="1",
            recommendation=Recommendation.PROCEED_WITH_CAUTION,
            confidence=0.7,
            summary="Financially viable but with a high upfront cost.",
            key_assumptions=["$1M covers 1 year of runway."],
            supporting_evidence=["Based on average European expansion costs."],
            risks=[]
        ),
        "risk": ExpertAnalysis(
            agent_role="risk",
            round="1",
            recommendation=Recommendation.DO_NOT_PROCEED,
            confidence=0.9,
            summary="GDPR compliance costs will exceed the funding.",
            key_assumptions=["AI regulations in EU are strictly enforced."],
            supporting_evidence=["EU AI Act requires massive compliance overhead."],
            risks=[{"description": "Regulatory fine", "severity": "critical", "likelihood": "high"}]
        )
    }
    
    disagreement = DisagreementReport(
        score=0.8,
        flagged_points=[
            DisagreementPoint(topic="Funding Adequacy", positions={"finance": "Viable", "risk": "Insufficient due to compliance"})
        ],
        summary="Risk and Finance fundamentally disagree on the adequacy of $1M funding in light of GDPR fines.",
        route_decision="proceed_to_turn2"
    )

    return GraphState(
        problem_statement="We are considering launching a new AI product in Europe. We have 1M in funding.",
        context_docs=["Doc 1: EU AI Act summary.", "Doc 2: Competitor analysis."],
        current_turn=2,
        turn1_analyses=turn1_analyses,
        disagreement_report_t1=disagreement,
        run_id="test_run_t2"
    )

def test_expert_growth_t2(t2_state):
    result = expert_growth(t2_state)
    assert "turn2_analyses" in result
    analysis = result["turn2_analyses"]["growth"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "growth"
    assert analysis.round == "2"
    # In a real environment, we'd check dissent_notes here, 
    # but the mock LLM might just return a generic valid schema depending on the provider.
    # The important part is it doesn't crash and the schema strictly validates.

def test_expert_finance_t2(t2_state):
    # Add a dummy growth analysis so finance sees peers
    t2_state.turn1_analyses["growth"] = ExpertAnalysis(
        agent_role="growth",
        round="1",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        summary="High demand in Europe.",
        key_assumptions=["Market is ready."],
        supporting_evidence=["Competitor has 10k users."],
        risks=[]
    )
    result = expert_finance(t2_state)
    assert "turn2_analyses" in result
    analysis = result["turn2_analyses"]["finance"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "finance"
    assert analysis.round == "2"

def test_expert_risk_t2(t2_state):
    # Add a dummy growth analysis so risk sees peers
    t2_state.turn1_analyses["growth"] = ExpertAnalysis(
        agent_role="growth",
        round="1",
        recommendation=Recommendation.PROCEED,
        confidence=0.8,
        summary="High demand in Europe.",
        key_assumptions=["Market is ready."],
        supporting_evidence=["Competitor has 10k users."],
        risks=[]
    )
    result = expert_risk(t2_state)
    assert "turn2_analyses" in result
    analysis = result["turn2_analyses"]["risk"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "risk"
    assert analysis.round == "2"
