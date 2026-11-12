"""Streamlit entry point: configures the app and connects the four guided workflow pages.

Run locally with ``streamlit run app.py``. Page rendering lives in ``ui/``; this
file only handles shared navigation, styling, and the sidebar.
"""
import streamlit as st

st.set_page_config(page_title="BizSage", page_icon="🍛", layout="wide", initial_sidebar_state="auto")

from ui import business, dashboard, investigation, results  # noqa: E402
from config import MIN_QUESTIONS_TO_VIEW_RESULTS  # noqa: E402
from ui.components import html  # noqa: E402
from ui.state import fresh, rs  # noqa: E402
from ui.theme import inject_css  # noqa: E402
from expert_system.reasoning_controller import ReasoningSession  # noqa: E402


def build_pages() -> dict:
    """Create the page registry once so navigation labels and destinations stay consistent."""
    P = st.Page
    return {
        "overview": P(dashboard.render, title="Start", icon=":material/home:", url_path="overview", default=True),
        "business": P(business.render, title="1. Business information", icon=":material/storefront:", url_path="business"),
        "investigation": P(investigation.render, title="2. Investigation", icon=":material/help_outline:", url_path="investigation"),
        "results": P(results.render, title="3. Findings and options", icon=":material/balance:", url_path="results"),
    }


def sidebar(pages: dict) -> None:
    """Show navigation and a clearly styled control to start a fresh assessment."""
    with st.sidebar:
        html('<div class="bs-brand">Biz<i>Sage</i></div><div class="bs-tag">Restaurant decision helper</div>')
        st.write("")
        s = rs()
        for page in pages.values():
            locked = page is pages["results"] and len(s.asked) < MIN_QUESTIONS_TO_VIEW_RESULTS
            st.page_link(
                page,
                disabled=locked,
                help="Answer at least 10 investigation questions to unlock findings."
                if locked else None,
            )
        st.divider()
        if s.has_data() and st.button("Start a new assessment", key="side_reset"):
            fresh(ReasoningSession())
            st.rerun()
        st.caption("Demo examples are fictional. BizSage supports your decision; it does not make it for you.")


inject_css()
pages = build_pages()
st.session_state["nav"] = pages
pg = st.navigation(list(pages.values()), position="hidden")
sidebar(pages)
pg.run()
