"""Start page: fictional examples, high-level progress, current trends, and next-step links."""
import streamlit as st

from expert_system import hypothesis_manager
from ui import charts
from ui.components import badge, bar, esc, go, header, html, kpi_row, money, note
from ui.state import CASES, CASE_KEYS, load_case, month_labels, rs


def _welcome():
    """Offer sample cases or a clear route to enter the user's own business data."""
    html('''<div class="bs-hero"><div class="bs-tag">Expert system + decision support</div>
        <div class="bs-title" style="margin-top:.4rem">Why is your restaurant's profit slipping?</div>
        <p class="bs-muted" style="max-width:46rem;margin-top:.5rem">BizSage investigates your restaurant like an expert would: it considers several possible causes at once,
        asks only the questions that matter, strengthens or rules out each cause as you answer, and then compares your options. You make the final decision.</p></div>''')
    st.markdown("##### Start with a Demo case")
    cols = st.columns(3)
    for col, key in zip(cols, CASE_KEYS):
        with col:
            c = CASES[key]
            html(f'<div class="bs-card"><h4>{esc(c["profile"]["city"])}</h4><p>{esc(c["title"])}</p></div>')
            if st.button("Load this case", key=f"dash_{key}", type="primary"):
                load_case(key)
                st.rerun()
    st.markdown("##### Or enter your own business")
    go("business", "Enter business information", primary=True)


def render():
    """Render the welcome view or summarize the active assessment."""
    header("Start", "Use a sample restaurant or enter your own information to get practical options.")
    s = rs()
    if not s.has_data():
        _welcome()
        return
    if s.state is None:
        s.analyze()
    stt = s.state
    d, hist = stt["derived"], stt["clean_history"]
    last = hist[-1] if hist else {}
    prof = s.profile
    st.markdown(f"**{esc(prof.get('name', 'Your business'))}** &nbsp;·&nbsp; {esc(prof.get('city', ''))} &nbsp;·&nbsp; {esc(prof.get('type', ''))}", unsafe_allow_html=True)
    # Count only findings above the same support threshold used for a primary conclusion.
    active = [h for h in stt["hypotheses"].values() if h.net is not None and h.net >= 0.4]
    chg = d.get("revenue_change_pct")
    profit, margin = d.get("net_profit"), d.get("net_margin_pct")
    kpi_row([
        {"label": "Monthly revenue", "value": money(last.get("revenue"), ""), "hint": "" if chg is None else f"{chg:+.1f}% vs previous month"},
        {"label": "Monthly expenses", "value": money(last.get("expenses"), ""), "hint": "" if d.get("food_cost_ratio") is None else f"Food {d['food_cost_ratio']:.0f}% of sales"},
        {"label": "Net profit", "value": money(profit, ""), "hint": "" if margin is None else f"{margin:.1f}% margin"},
        {"label": "Likely causes found", "value": len(active), "hint": f"{stt['completeness']['completeness_pct']}% of data provided"},
    ])
    html(f'<div class="bs-card"><h4>Expert system status {badge("Investigation open" if not s.termination() else "Investigation complete", "info" if not s.termination() else "success")}</h4>'
         f'<p>{esc(s.summary_text())}</p></div>')
    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        charts.show(charts.revenue_expenses(month_labels(s), hist))
    with c2:
        st.markdown("##### Top findings so far")
        top = [h for h in hypothesis_manager.ranked(stt["hypotheses"]) if h.net is not None][:5]
        for h in top:
            html(f'<div class="bs-card" style="padding:.6rem .9rem"><div style="display:flex;justify-content:space-between;gap:.5rem"><b style="font-size:.9rem">{esc(h.name)}</b>{badge(h.label, h.tone)}</div>{bar(max(h.score, 0) * 100, h.score < 0)}</div>')
    b1, b2, b3 = st.columns(3)
    with b1:
        go("business", "Update business information")
    with b2:
        go("investigation", "Continue the investigation", primary=True)
    with b3:
        go("results", "Review findings and options")
    if stt["conflicts"] or any(i.severity in ("error", "warning") for i in stt["issues"]):
        note("Some data needs your attention. Open Findings and options to review warnings and conflicts.", "Data quality")
