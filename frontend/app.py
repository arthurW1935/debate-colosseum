"""Debate Colosseum — Streamlit frontend.

D5: Problem input form + file upload
D6: Live debate timeline (polls /status)
D7: Decision memo review UI
D8: HITL controls (Approve / Feedback / Abandon) wired to POST /runs/{id}/review

Run with:
    streamlit run frontend/app.py
Backend must be running on http://localhost:8000.
"""

import time
from typing import Optional

import requests
import streamlit as st

API_BASE = "http://localhost:8000"
POLL_INTERVAL_SECONDS = 2


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_create_run(problem_statement: str, files: list) -> Optional[dict]:
    data = {"problem_statement": problem_statement}
    uploaded = [("files", (f.name, f.getvalue(), f.type)) for f in files] if files else []
    try:
        resp = requests.post(f"{API_BASE}/runs", data=data, files=uploaded or None, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Failed to start run: {exc}")
        return None


def api_get_status(run_id: str) -> Optional[dict]:
    try:
        resp = requests.get(f"{API_BASE}/runs/{run_id}/status", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Status poll failed: {exc}")
        return None


def api_submit_review(run_id: str, decision: str, feedback_text: Optional[str] = None) -> Optional[dict]:
    payload: dict = {"decision": decision}
    if feedback_text:
        payload["feedback_text"] = feedback_text
    try:
        resp = requests.post(f"{API_BASE}/runs/{run_id}/review", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.error(f"Review submission failed: {exc}")
        return None


# ---------------------------------------------------------------------------
# Page sections
# ---------------------------------------------------------------------------

def render_problem_input() -> None:
    """D5: Problem input form and file upload."""
    st.title("Debate Colosseum")
    st.caption("Multi-agent AI platform for complex business decisions")
    st.divider()

    with st.form("problem_form"):
        problem = st.text_area(
            "Describe the decision you need to make",
            placeholder=(
                "e.g. Should we expand into the EU market next quarter? "
                "We currently have €2M ARR, 3 engineers, and no EU legal entity."
            ),
            height=160,
        )
        uploaded_files = st.file_uploader(
            "Upload supporting documents (optional)",
            type=["pdf", "txt", "md"],
            accept_multiple_files=True,
            help="PDFs and plain-text documents — context for the expert agents.",
        )

        if uploaded_files:
            st.caption(f"**{len(uploaded_files)} file(s) ready:**")
            for f in uploaded_files:
                st.write(f"  • {f.name} ({f.size:,} bytes)")

        submitted = st.form_submit_button("Start Debate", type="primary", use_container_width=True)

    if submitted:
        if not problem.strip():
            st.warning("Please enter a problem statement before starting.")
            return
        with st.spinner("Starting debate run…"):
            result = api_create_run(problem.strip(), uploaded_files)
        if result:
            st.session_state["run_id"] = result["run_id"]
            st.session_state["status"] = "running"
            st.rerun()


def render_timeline(status_data: dict) -> None:
    """D6: Debate timeline derived from current run status."""
    status = status_data.get("status", "running")
    turn = status_data.get("current_turn", 1)
    feedback_round = status_data.get("feedback_round", 0)
    has_memo = status_data.get("final_memo") is not None

    st.subheader("Debate Timeline")

    phases = [
        ("Context Ingestion", True),
        ("Turn 1 — Expert Analysis (Growth · Finance · Risk)", True),
        ("Moderator — Disagreement Scoring", turn >= 1),
        ("Turn 2 — Peer-Aware Revision", turn >= 2),
        ("Arbiter (if disagreement persists)", has_memo),
        ("Synthesizer — Decision Memo", has_memo),
        ("Guardrail Check", status_data.get("guardrail_passed", False)),
        ("Human Review", status in ("awaiting_review", "completed")),
    ]

    for label, done in phases:
        icon = "✅" if done else ("⏳" if status == "running" else "⬜")
        st.write(f"{icon}  {label}")

    if feedback_round > 0:
        st.write(f"🔄  Feedback loop — round {feedback_round}")

    st.divider()

    if status == "running":
        st.info("Running… auto-refreshing every few seconds.")
    elif status == "error":
        st.error(f"Run failed: {status_data.get('error', 'unknown error')}")
    elif status == "completed":
        action = status_data.get("action_status") or "no action"
        st.success(f"Run complete — external action: **{action}**")


def render_risk_register(risks: list[dict]) -> None:
    if not risks:
        return
    st.markdown("**Risk Register**")
    cols = st.columns([3, 1, 1, 2])
    cols[0].caption("Description")
    cols[1].caption("Severity")
    cols[2].caption("Likelihood")
    cols[3].caption("Mitigation")
    for r in risks:
        severity_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
            r.get("severity", ""), "⚪"
        )
        cols = st.columns([3, 1, 1, 2])
        cols[0].write(r.get("description", ""))
        cols[1].write(f"{severity_color} {r.get('severity', '')}")
        cols[2].write(r.get("likelihood", ""))
        cols[3].write(r.get("mitigation") or "—")


def render_expert_positions(positions: list) -> None:
    if not positions:
        return
    st.markdown("**Expert Positions**")
    tabs = st.tabs([p.get("agent_role", "expert").capitalize() for p in positions])
    for tab, analysis in zip(tabs, positions):
        with tab:
            rec = analysis.get("recommendation", "—")
            conf = analysis.get("confidence", 0)
            st.write(f"**Recommendation:** `{rec}` — Confidence: {conf:.0%}")
            st.write(analysis.get("summary", ""))
            if analysis.get("dissent_notes"):
                st.info(f"**Dissent:** {analysis['dissent_notes']}")
            assumptions = analysis.get("key_assumptions", [])
            if assumptions:
                with st.expander("Key assumptions"):
                    for a in assumptions:
                        st.write(f"• {a}")


def render_memo(memo: dict) -> None:
    """D7: Render all DecisionMemo sections."""
    rec = memo.get("recommendation", "").upper()
    conf = memo.get("confidence", 0)
    revision = memo.get("feedback_revision_count", 0)

    badge_color = {
        "PROCEED": "green",
        "PROCEED-WITH-CAUTION": "orange",
        "DO-NOT-PROCEED": "red",
    }.get(rec, "grey")

    st.subheader("Decision Memo")
    st.markdown(
        f"**Recommendation:** :{badge_color}[{rec}]  |  "
        f"**Confidence:** {conf:.0%}"
        + (f"  |  *Revision #{revision}*" if revision else "")
    )
    st.divider()

    st.markdown("### Executive Summary")
    st.write(memo.get("executive_summary", ""))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Key Agreements**")
        for a in memo.get("key_agreements", []):
            st.write(f"✓ {a}")
    with col2:
        st.markdown("**Key Disagreements**")
        for d in memo.get("key_disagreements", []):
            st.write(f"⚡ {d}")

    if memo.get("arbitration_summary"):
        st.markdown("**Arbitration Summary**")
        st.info(memo["arbitration_summary"])

    st.markdown("### Next Steps")
    for i, step in enumerate(memo.get("next_steps", []), 1):
        st.write(f"{i}. {step}")

    render_risk_register(memo.get("risk_register", []))
    render_expert_positions(memo.get("expert_positions", []))

    generated = memo.get("generated_at", "")
    if generated:
        st.caption(f"Generated at {generated}")


def render_hitl_controls(run_id: str) -> None:
    """D8: Approve / Feedback / Abandon controls."""
    st.subheader("Your Review")
    st.write("Please review the memo above and choose an action.")

    col_approve, col_feedback, col_abandon = st.columns(3)

    with col_approve:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            with st.spinner("Sending memo to Slack…"):
                result = api_submit_review(run_id, "approved")
            if result:
                st.session_state["status"] = "running"
                st.success("Approved — memo sent!")
                time.sleep(1)
                st.rerun()

    with col_feedback:
        if st.button("💬 Send Feedback", use_container_width=True):
            st.session_state["show_feedback_form"] = True
            st.rerun()

    with col_abandon:
        if st.button("🗑️ Abandon", use_container_width=True):
            with st.spinner("Abandoning run…"):
                result = api_submit_review(run_id, "abandoned")
            if result:
                st.session_state["status"] = "completed"
                st.warning("Run abandoned — state saved, no action taken.")
                time.sleep(1)
                st.rerun()

    # Inline feedback form (shown when user clicks Send Feedback)
    if st.session_state.get("show_feedback_form"):
        st.divider()
        with st.form("feedback_form"):
            feedback = st.text_area(
                "Feedback for the agents",
                placeholder=(
                    "e.g. The Finance agent missed the headcount dependency. "
                    "Please re-check the burn rate assumption."
                ),
                height=120,
            )
            col_submit, col_cancel = st.columns(2)
            submit = col_submit.form_submit_button("Submit Feedback", type="primary")
            cancel = col_cancel.form_submit_button("Cancel")

        if cancel:
            st.session_state["show_feedback_form"] = False
            st.rerun()

        if submit:
            if not feedback.strip():
                st.warning("Please enter feedback before submitting.")
            else:
                with st.spinner("Submitting feedback…"):
                    result = api_submit_review(run_id, "feedback", feedback.strip())
                if result:
                    st.session_state["show_feedback_form"] = False
                    st.session_state["status"] = "running"
                    st.info("Feedback submitted — re-processing the debate.")
                    time.sleep(1)
                    st.rerun()


# ---------------------------------------------------------------------------
# Main app loop
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="Debate Colosseum",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Initialise session state keys
    if "run_id" not in st.session_state:
        st.session_state["run_id"] = None
    if "status" not in st.session_state:
        st.session_state["status"] = None
    if "show_feedback_form" not in st.session_state:
        st.session_state["show_feedback_form"] = False

    run_id: Optional[str] = st.session_state["run_id"]

    # ── No active run: show input form ──────────────────────────────────────
    if run_id is None:
        render_problem_input()
        return

    # ── Active run: poll status and render accordingly ─────────────────────
    status_data = api_get_status(run_id)
    if status_data is None:
        st.error("Could not reach the backend. Is it running on localhost:8000?")
        if st.button("Start over"):
            st.session_state["run_id"] = None
            st.rerun()
        return

    current_status = status_data["status"]
    st.session_state["status"] = current_status

    # Sidebar: run metadata
    with st.sidebar:
        st.markdown("### Run Info")
        st.code(run_id, language=None)
        st.write(f"**Status:** `{current_status}`")
        st.write(f"**Turn:** {status_data.get('current_turn', 1)}")
        fb = status_data.get("feedback_round", 0)
        if fb:
            st.write(f"**Feedback rounds:** {fb}")
        if st.button("← New debate"):
            st.session_state["run_id"] = None
            st.session_state["status"] = None
            st.rerun()

    # D6: Timeline always visible
    render_timeline(status_data)

    # D7 + D8: Memo and HITL controls when awaiting review
    if current_status == "awaiting_review":
        memo = status_data.get("final_memo")
        if memo:
            render_memo(memo)
            st.divider()
            render_hitl_controls(run_id)
        else:
            st.info("Memo not yet available — waiting for synthesis to complete.")

    elif current_status == "completed":
        memo = status_data.get("final_memo")
        if memo:
            render_memo(memo)
        action = status_data.get("action_status")
        if action:
            st.success(f"External action: **{action}**")

    elif current_status == "error":
        st.error(f"Error: {status_data.get('error', 'unknown')}")
        if st.button("Start over"):
            st.session_state["run_id"] = None
            st.rerun()

    # Auto-refresh while running
    if current_status == "running":
        time.sleep(POLL_INTERVAL_SECONDS)
        st.rerun()


if __name__ == "__main__":
    main()
