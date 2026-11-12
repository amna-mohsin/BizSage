"""Small, escaped HTML and Streamlit helpers shared across the user interface."""
from html import escape as esc
from typing import List

import streamlit as st

from config import IDENTITY


def clean(s: str) -> str:
    """Trim blank lines from trusted, hand-authored HTML snippets."""
    return "\n".join(line.strip() for line in s.strip().splitlines() if line.strip())


def html(s: str) -> None:
    """Render a component snippet; callers must escape any user-provided text first."""
    st.markdown(clean(s), unsafe_allow_html=True)


def identification() -> None:
    """Show the project identity without exposing personal student information."""
    html(f'<div class="bs-id"><span><b>{esc(IDENTITY["project"])}</b> &middot; {esc(IDENTITY["subtitle"])}</span>'
         '</div>')


def header(title: str, subtitle: str = "") -> None:
    identification()
    html(f'<div class="bs-title">{esc(title)}</div><div class="bs-sub">{esc(subtitle)}</div>')


def badge(text: str, tone: str = "neutral") -> str:
    """Build a compact, escaped status label."""
    return f'<span class="bs-badge t-{tone}">{esc(str(text))}</span>'


def kpi(label: str, value, hint: str = "") -> str:
    """Build one metric card for the dashboard's high-level summary."""
    h = f'<div class="h">{esc(hint)}</div>' if hint else ""
    return f'<div class="bs-card bs-kpi"><div class="l">{esc(label)}</div><div class="v">{esc(str(value))}</div>{h}</div>'


def kpi_row(items: List[dict]) -> None:
    """Lay out related metrics together so responsive CSS can adapt the whole group."""
    with st.container(key="bs-kpi-row"):
        for col, it in zip(st.columns(len(items)), items):
            with col:
                html(kpi(**it))


def bar(pct: float, bad: bool = False) -> str:
    """Render a clamped 0-100 support bar; negative evidence receives a warning color."""
    pct = max(0, min(100, pct))
    return f'<div class="bs-bar {"bad" if bad else ""}"><div style="width:{pct}%"></div></div>'


def note(text: str, title: str = "") -> None:
    t = f"<b>{esc(title)}:</b> " if title else ""
    html(f'<div class="bs-note">{t}{text}</div>')


def money(v, prefix="Rs ") -> str:
    return "n/a" if v is None else f"{prefix}{v:,.0f}"


def table(rows: List[List[str]], headers: List[str]) -> None:
    """Render an overflow-safe table; row values are pre-escaped by the caller."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    html(f'<div class="bs-card" style="padding:.4rem .6rem;overflow-x:auto"><table class="bs-table"><tr>{head}</tr>{body}</table></div>')


def go(key: str, label: str, primary: bool = False, disabled: bool = False) -> None:
    """Navigate to a registered workflow page after the user selects its button."""
    if st.button(label, type="primary" if primary else "secondary", key=f"go_{key}_{label}", disabled=disabled):
        st.switch_page(st.session_state["nav"][key])
