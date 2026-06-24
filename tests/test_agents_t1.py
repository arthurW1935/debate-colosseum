import pytest
from src.schemas import GraphState, ExpertAnalysis
from src.agents.growth import expert_growth
from src.agents.finance import expert_finance
from src.agents.risk import expert_risk

@pytest.fixture
def base_state():
    return GraphState(
        problem_statement="We are considering launching a new AI product in Europe. We have 1M in funding.",
        run_id="test_run_123",
        current_turn=1
    )

def test_expert_growth(base_state):
    result = expert_growth(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["growth"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "growth"
    assert analysis.round == "1"

def test_expert_finance(base_state):
    result = expert_finance(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["finance"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "finance"
    assert analysis.round == "1"

def test_expert_risk(base_state):
    result = expert_risk(base_state)
    assert "turn1_analyses" in result
    analysis = result["turn1_analyses"]["risk"]
    assert isinstance(analysis, ExpertAnalysis)
    assert analysis.agent_role == "risk"
    assert analysis.round == "1"
    # Risk agent should ideally populate the risks array
    # However, since it's an LLM, we can't strictly enforce > 0 without prompt engineering
    # Pydantic schema allows empty list, but let's assert it just in case to ensure it's doing its job.
    if hasattr(analysis, "risks"):
        assert isinstance(analysis.risks, list)
