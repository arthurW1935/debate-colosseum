import pytest
from src.schemas import GraphState, ExpertAnalysis
from src.agents.growth import expert_growth
from src.agents.finance import expert_finance
from src.agents.risk import expert_risk

@pytest.fixture
def base_state():
    initial_state = GraphState(
        problem_statement="Should we expand into the EU market? (Scenario 1)",
        run_id="test_run_e2e",
        current_turn=1,
        context_docs=[
            "synthetic_docs/00_company_profile.md",
            "synthetic_docs/01_financial_projections_fy25_fy27.md",
            "synthetic_docs/02_eu_market_expansion_research.md",
            "synthetic_docs/06_market_research_consumer_insights.md",
            "synthetic_docs/07_risk_register.md",
            "synthetic_docs/08_board_meeting_minutes_jan2025.md"
        ]
    )
    from src.rag.ingest import ingest_context
    result_dict = ingest_context(initial_state)
    initial_state.retriever = result_dict["retriever"]
    return initial_state

def test_e2e_expert_growth(base_state):
    result = expert_growth(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["growth"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "growth"
    assert analysis.round == "1"

def test_e2e_expert_finance(base_state):
    result = expert_finance(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["finance"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "finance"
    assert analysis.round == "1"

def test_e2e_expert_risk(base_state):
    result = expert_risk(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["risk"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "risk"
    assert analysis.round == "1"
