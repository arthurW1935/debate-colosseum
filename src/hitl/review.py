"""HITL review helpers.

Applies the human's review decision to the current GraphState so the graph
can resume correctly.  The actual graph resumption is handled by the FastAPI
layer (src/api/main.py); this module owns only the pure state-mutation logic
so it can be tested independently.
"""

import logging
from typing import Literal, Optional

from src.schemas import GraphState, HumanFeedbackEntry

logger = logging.getLogger(__name__)


def handle_review(
    state: GraphState,
    decision: Literal["approved", "feedback", "abandoned"],
    feedback_text: Optional[str] = None,
    edited_memo: Optional[dict] = None,
) -> GraphState:
    """Return a new GraphState with the human review decision applied.

    Args:
        state: Current graph state (not mutated — a deep copy is returned).
        decision: The human's action: approve, request feedback, or abandon.
        feedback_text: Required when decision == "feedback".
        edited_memo: Optional dict of DecisionMemo fields the human modified
                     directly in the UI before approving.

    Returns:
        Updated GraphState ready for graph resumption.
    """
    updated = state.model_copy(deep=True)
    updated.human_decision = decision

    if decision == "feedback":
        if not feedback_text:
            raise ValueError("feedback_text is required when decision == 'feedback'")

        updated.feedback_round += 1
        updated.current_feedback_text = feedback_text

        entry = HumanFeedbackEntry(
            feedback_text=feedback_text,
            feedback_round=updated.feedback_round,
            # Placeholder — the synthesizer/agent nodes will overwrite this
            # field once they determine how the feedback was resolved.
            resolved_by="synthesizer_only",
            target_agent_if_any=None,
            contradiction_detected=False,
        )
        updated.human_feedback_history = updated.human_feedback_history + [entry]
        logger.info(
            "Feedback round %d registered for run_id=%s",
            updated.feedback_round,
            updated.run_id,
        )

    elif decision == "approved":
        if edited_memo:
            # Human may have tweaked memo text in the UI; apply the overrides.
            from src.schemas import DecisionMemo

            if updated.final_memo is not None:
                # Only update fields the human actually sent.
                merged = updated.final_memo.model_dump()
                merged.update(edited_memo)
                updated.final_memo = DecisionMemo.model_validate(merged)
        logger.info("Run approved for run_id=%s", updated.run_id)

    elif decision == "abandoned":
        # If there's an open feedback entry, mark it as abandoned.
        if updated.human_feedback_history:
            last = updated.human_feedback_history[-1]
            if last.resolved_by == "synthesizer_only":
                patched = last.model_copy(update={"resolved_by": "abandoned"})
                updated.human_feedback_history = (
                    updated.human_feedback_history[:-1] + [patched]
                )
        logger.info("Run abandoned for run_id=%s", updated.run_id)

    return updated
