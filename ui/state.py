"""Session-state helpers for demo loading, navigation readiness, and resetting widget data.

The application uses no database: the active ReasoningSession lives only in the current
Streamlit browser session.
"""
import json
from pathlib import Path

import streamlit as st

from expert_system.reasoning_controller import ReasoningSession

CASES = json.loads((Path(__file__).resolve().parent.parent / "demo_data" / "cases.json").read_text(encoding="utf-8"))
CASE_KEYS = ["karachi_family_restaurant", "lahore_cafe_cash_pressure", "highway_dhaba_weekend_peak"]


def rs() -> ReasoningSession:
    """Return the current reasoning session, creating a clean one for a new visitor."""
    if "rs" not in st.session_state:
        st.session_state["rs"] = ReasoningSession()
    return st.session_state["rs"]


DEFAULT_MONTHS = ["5 months ago", "4 months ago", "3 months ago", "2 months ago", "Last month", "Current month"]


def month_labels(session: ReasoningSession):
    """Use saved month names when present and fill missing labels with readable defaults."""
    labels = session.profile.get("months") or DEFAULT_MONTHS
    n = len(session.history)
    return (list(labels) + DEFAULT_MONTHS)[:n] if len(labels) < n else list(labels)[:n]


def fresh(session: ReasoningSession) -> None:
    """Replace the case and clear related widget state so old form values cannot leak across cases."""
    st.session_state["rs"] = session
    for k in ("dss_weights", "dss_assumptions", "decisions", "branch_data"):
        st.session_state.pop(k, None)
    for k in list(st.session_state.keys()):                # forget old widget values so forms show the new data
        if k.startswith(("in_", "prof_", "hist_", "be_", "bn_", "ans_", "dec_")):
            del st.session_state[k]


def load_case(key: str) -> None:
    """Start a new reasoning session from a bundled demo  example."""
    c = CASES[key]
    s = ReasoningSession()
    s.set_inputs(dict(c["raw"]), [dict(r) for r in c["history"]], dict(c["profile"]))
    s.profile["demo_case"] = key
    s.analyze()
    fresh(s)


def ready() -> bool:
    s = rs()
    return s.has_data() and s.state is not None


def require_data() -> None:
    """Stop a protected page early when no assessment exists, or analyze it if needed."""
    s = rs()
    if not s.has_data():
        st.info("No business data yet. Start by entering figures on the Business information page, or load a demo  example from Start.")
        st.stop()
    if s.state is None:
        s.analyze()
