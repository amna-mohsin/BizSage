"""Combined evidence summary and owner-controlled decision support."""
import streamlit as st

from ui import decision_center, diagnosis
from ui.components import header


def render():
    """Place diagnosis and actionable alternatives in one final review step."""
    header(
        "Findings and options",
        "See what the evidence suggests, compare practical options, and make the final decision yourself.",
    )
    st.markdown("#### A. What the evidence suggests")
    diagnosis.render(show_header=False)
    st.divider()
    st.markdown("#### B. Compare possible actions")
    decision_center.render(show_header=False)
