from pydantic import BaseModel, Field
from typing import Literal, Optional, Any, Annotated
from enum import Enum
import operator

def merge_dict(left: dict, right: dict) -> dict:
    if left is None: left = {}
    if right is None: right = {}
    return {**left, **right}


class Recommendation(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CAUTION = "proceed-with-caution"
    DO_NOT_PROCEED = "do-not-proceed"

class RiskItem(BaseModel):
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    likelihood: Literal["low", "medium", "high"]
    mitigation: Optional[str] = None

class ExpertAnalysis(BaseModel):
    agent_role: Literal["growth", "finance", "risk"]
    round: Literal[1, 2, "feedback"]
    recommendation: Recommendation
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str
    key_assumptions: list[str]
    supporting_evidence: list[str]
    risks: list[RiskItem]
    dissent_notes: Optional[str] = None
    feedback_context: Optional[str] = None

class DisagreementPoint(BaseModel):
    topic: str
    positions: dict[str, str]

class DisagreementReport(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    flagged_points: list[DisagreementPoint]
    summary: str
    route_decision: Literal["skip_to_synthesis", "proceed_to_turn2", "proceed_to_arbiter"]

class ArbitrationResult(BaseModel):
    rulings: list[dict]
    unresolved_points: list[str]

class DecisionMemo(BaseModel):
    executive_summary: str
    recommendation: Recommendation
    confidence: float
    expert_positions: dict[str, ExpertAnalysis]
    key_agreements: list[str]
    key_disagreements: list[str]
    arbitration_summary: Optional[str] = None
    risk_register: list[RiskItem]
    next_steps: list[str]
    generated_at: str
    feedback_revision_count: int = 0

class SynthesizerFeedbackDecision(BaseModel):
    """Synthesizer's routing decision on a feedback round."""
    requires_agent_revision: bool
    target_agent: Optional[Literal["growth", "finance", "risk"]] = None
    revised_memo: Optional[DecisionMemo] = None
    reasoning: str

class HumanFeedbackEntry(BaseModel):
    feedback_text: str
    feedback_round: int
    resolved_by: Literal["synthesizer_only", "targeted_agent", "abandoned"]
    target_agent_if_any: Optional[Literal["growth", "finance", "risk"]] = None
    contradiction_detected: bool = False

class GraphState(BaseModel):
    problem_statement: str
    context_docs: Annotated[list[str], operator.add] = []
    retriever: Optional[Any] = None
    turn1_analyses: Annotated[dict[str, ExpertAnalysis], merge_dict] = {}
    turn2_analyses: Annotated[dict[str, ExpertAnalysis], merge_dict] = {}
    feedback_analyses: Annotated[dict[str, ExpertAnalysis], merge_dict] = {}
    disagreement_report_t1: Optional[DisagreementReport] = None
    disagreement_report_t2: Optional[DisagreementReport] = None
    arbitration_result: Optional[ArbitrationResult] = None
    final_memo: Optional[DecisionMemo] = None
    guardrail_passed: bool = False
    human_decision: Optional[Literal["approved", "feedback", "abandoned"]] = None
    current_feedback_text: Optional[str] = None
    human_feedback_history: Annotated[list[HumanFeedbackEntry], operator.add] = []
    action_status: Optional[str] = None
    current_turn: int = 1
    feedback_round: int = 0
    run_id: str
