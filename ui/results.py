"""Combined evidence summary and owner-controlled decision support."""
import streamlit as st

from config import MIN_QUESTIONS_TO_VIEW_RESULTS
from ui import decision_center, diagnosis
from ui.components import go, header
from ui.state import required_answers_remaining, rs


def render():
    """Place diagnosis and actionable alternatives in one final review step."""
    header(
        "Findings and options",
        "See what the evidence suggests, compare practical options, and make the final decision yourself.",
    )
    remaining = required_answers_remaining(rs())
    if remaining:
        answered = MIN_QUESTIONS_TO_VIEW_RESULTS - remaining
        st.info(
            f"Answer at least {MIN_QUESTIONS_TO_VIEW_RESULTS} investigation questions before viewing findings. "
            f"You have answered {answered} so far."
        )
        go("investigation", "Continue the investigation", primary=True)
        st.stop()
    st.markdown("#### A. What the evidence suggests")
    diagnosis.render(show_header=False)
    st.divider()
    st.markdown("#### B. Compare possible actions")
    decision_center.render(show_header=False)
