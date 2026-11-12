"""Streamlit entry point: configures the app and connects the four guided workflow pages.

Run locally with ``streamlit run app.py``. Page rendering lives in ``ui/``; this
file only handles shared navigation, styling, and the sidebar.
"""
import streamlit as st

st.set_page_config(page_title="BizSage", page_icon=":material/insights:", layout="wide", initial_sidebar_state="auto")

from ui import business, dashboard, investigation, results  # noqa: E402
from ui.components import bar, html  # noqa: E402
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
    """Show navigation and assessment progress shared by all pages."""
    with st.sidebar:
        html('<div class="bs-brand">Biz<i>Sage</i></div><div class="bs-tag">Restaurant decision helper</div>')
        st.write("")
        for page in pages.values():
            st.page_link(page)
        st.divider()
        s = rs()
        if s.has_data() and s.state:
            comp = s.state["completeness"]["completeness_pct"]
            html(f'<div class="bs-muted">Data completeness: <b>{comp}%</b></div>{bar(comp)}'
                 f'<div class="bs-muted">Questions answered: <b>{len(s.asked)}</b></div>')
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
