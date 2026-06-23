from langgraph.graph import StateGraph, START, END
from src.schemas import GraphState

from src.rag.ingest import ingest_context
from src.agents.growth import expert_growth
from src.agents.finance import expert_finance
from src.agents.risk import expert_risk
from src.agents.moderator import moderator_t1, moderator_t2
from src.agents.arbiter import arbiter
from src.agents.synthesiser import synthesizer
from src.guardrails.checks import guardrail_check


def human_review(state: GraphState) -> GraphState:
    """Dummy node to serve as the interrupt point for HITL."""
    return state


def build_graph(checkpointer=None):
    workflow = StateGraph(GraphState)
    
    # --------------------------------------------------------------------------
    # Checkpoint 2: Node Registration
    # --------------------------------------------------------------------------
    workflow.add_node("ingest_context", ingest_context)
    
    # Turn 1 Agents
    workflow.add_node("expert_growth", expert_growth)
    workflow.add_node("expert_finance", expert_finance)
    workflow.add_node("expert_risk", expert_risk)
    
    # Moderators
    workflow.add_node("moderator_t1", moderator_t1)
    workflow.add_node("moderator_t2", moderator_t2)
    
    # Turn 2 Agents
    workflow.add_node("expert_growth_r2", expert_growth)
    workflow.add_node("expert_finance_r2", expert_finance)
    workflow.add_node("expert_risk_r2", expert_risk)
    
    # Arbiter
    workflow.add_node("arbiter", arbiter)
    
    # Synthesizer
    workflow.add_node("synthesizer", synthesizer)
    
    # Feedback Agents (targeted re-runs)
    workflow.add_node("expert_growth_fb", expert_growth)
    workflow.add_node("expert_finance_fb", expert_finance)
    workflow.add_node("expert_risk_fb", expert_risk)
    
    # Guardrails and HITL
    workflow.add_node("guardrail_check", guardrail_check)
    workflow.add_node("human_review", human_review)

    # --------------------------------------------------------------------------
    # Checkpoint 3: Edges and Conditional Routing
    # --------------------------------------------------------------------------
    
    # 1. START -> ingest_context
    workflow.add_edge(START, "ingest_context")
    
    # 2. ingest_context -> Turn 1 parallel fan-out
    workflow.add_edge("ingest_context", "expert_growth")
    workflow.add_edge("ingest_context", "expert_finance")
    workflow.add_edge("ingest_context", "expert_risk")
    
    # 3. Turn 1 agents -> moderator_t1
    workflow.add_edge("expert_growth", "moderator_t1")
    workflow.add_edge("expert_finance", "moderator_t1")
    workflow.add_edge("expert_risk", "moderator_t1")
    
    # 4. moderator_t1 conditional routing
    def route_after_t1(state: GraphState):
        if state.disagreement_report_t1.route_decision == "skip_to_synthesis":
            return "synthesizer"
        return ["expert_growth_r2", "expert_finance_r2", "expert_risk_r2"]
    
    workflow.add_conditional_edges("moderator_t1", route_after_t1)
    
    # 5. Turn 2 agents -> moderator_t2
    workflow.add_edge("expert_growth_r2", "moderator_t2")
    workflow.add_edge("expert_finance_r2", "moderator_t2")
    workflow.add_edge("expert_risk_r2", "moderator_t2")
    
    # 6. moderator_t2 conditional routing
    def route_after_t2(state: GraphState):
        if state.disagreement_report_t2.route_decision == "skip_to_synthesis":
            return "synthesizer"
        return "arbiter"
        
    workflow.add_conditional_edges("moderator_t2", route_after_t2)
    
    # 7. Arbiter -> synthesizer
    workflow.add_edge("arbiter", "synthesizer")
    
    # --------------------------------------------------------------------------
    # Checkpoint 4: Feedback Loops, Guardrails, and Interrupt Edges
    # --------------------------------------------------------------------------
    
    # 8. synthesizer conditional routing
    def route_after_synthesizer(state: GraphState):
        if state.action_status and state.action_status.startswith("revision_required:"):
            target_agent = state.action_status.split(":")[1]
            return f"expert_{target_agent}_fb"
        return "guardrail_check"
        
    workflow.add_conditional_edges("synthesizer", route_after_synthesizer)
    
    # 9. Feedback agents -> synthesizer
    workflow.add_edge("expert_growth_fb", "synthesizer")
    workflow.add_edge("expert_finance_fb", "synthesizer")
    workflow.add_edge("expert_risk_fb", "synthesizer")
    
    # 10. guardrail_check -> human_review
    workflow.add_edge("guardrail_check", "human_review")
    
    # 11. human_review conditional routing to END or synthesizer
    def route_after_human_review(state: GraphState):
        if state.human_decision == "approved" or state.human_decision == "abandoned":
            return END
        # state.human_decision == "feedback"
        return "synthesizer"
        
    workflow.add_conditional_edges("human_review", route_after_human_review)
    
    # Compile with human_review as an interrupt point for HITL
    return workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"]
    )
