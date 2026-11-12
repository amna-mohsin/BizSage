"""Compose the profile/history form and current-month assessment into one guided page."""
import streamlit as st

from ui import assessment, business_profile
from ui.components import header


def render():
    """Show the two related data-entry sections in the intended order."""
    header(
        "Business information",
        "Enter what you know. You can leave unknown figures blank; BizSage will not treat them as zero.",
    )
    st.markdown("#### A. Restaurant and recent monthly figures")
    business_profile.render(show_header=False)
    st.divider()
    st.markdown("#### B. This month's business details")
    assessment.render(show_header=False)
