"""Owner-controlled option comparison, configurable scoring, estimates, and branch analysis."""
import pandas as pd
import streamlit as st

from config import ASSUMPTIONS
from decision_support import branches as br
from decision_support import dss
from expert_system.knowledge_loader import load_kb
from ui import charts
from ui.components import badge, esc, header, html, money, note
from ui.state import CASES, require_data, rs

kb = load_kb()
LABELS = {c["id"]: c["label"] for c in kb.strategies["criteria"]}
ASSUMP_LABELS = {"target_customers_per_staff": "Customers one staff member can serve per day", "lost_sales_pct_overloaded": "Weekend sales lost when overloaded (%)",
                 "workforce_cut_pct": "Labour saved by a workforce cut (%)", "revenue_loss_after_cut_pct": "Revenue lost after a cut (%)",
                 "target_wastage_pct": "Wastage target (%)", "wastage_capture_pct": "Avoidable waste actually saved (%)",
                 "supplier_saving_pct": "Saving from supplier renegotiation (%)", "menu_margin_gain_pct": "Margin gained by menu changes (% of revenue)",
                 "discount_cut_pct": "Discounts removed (%)", "discount_volume_loss_pct": "Recovered discount lost as volume (%)",
                 "receivable_recovery_pct": "Overdue receivables collected (%)", "supplier_extra_days": "Extra supplier credit days",
                 "installment_relief_pct": "Instalment reduction (%)", "utility_saving_pct": "Utility saving (%)",
                 "branch_transfer_pct": "Customers moving to another branch (%)", "branch_close_cost_pct": "Closed-branch cost that cannot be avoided (%)",
                 "branch_delivery_cost_cut_pct": "Cost saved as delivery-only (%)", "branch_delivery_revenue_loss_pct": "Revenue lost as delivery-only (%)"}


def weights():
    """Keep user-selected scoring priorities in Streamlit session state."""
    return st.session_state.setdefault("dss_weights", dss.default_weights(kb))


def assumptions():
    """Keep editable estimate assumptions separate from measured business facts."""
    return st.session_state.setdefault("dss_assumptions", dict(ASSUMPTIONS))


def option_cards(options, title):
    """Show each option's rank, trade-offs, estimate, and score explanation."""
    charts.show(charts.dss_scores(options))
    for o in options:
        est = o["estimate"]
        net = est.get("monthly_net")
        eff = []
        if est["available"]:
            if net is not None:
                eff.append(f"Estimated monthly effect: <b>{money(net)}</b>")
            if est.get("one_time_cash") is not None:
                eff.append(f"One-time cash effect: <b>{money(est['one_time_cash'])}</b>")
        else:
            eff.append("Estimate unavailable. Missing: " + ", ".join(est["missing"]))
        top = "success" if o["rank"] == 1 else "neutral"
        html(f'<div class="bs-card"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem"><h4 style="margin:0">#{o["rank"]} {esc(o["name"])}</h4>'
             f'<span>{badge("Suitability " + format(o["weighted"], ".0f") + "/100", top)}</span></div><p>{esc(o["summary"])}</p><p>{" &middot; ".join(eff)}</p></div>')
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Advantages**")
            for p in o["pros"]:
                st.markdown(f"- {p}")
        with c2:
            st.markdown("**Disadvantages and risks**")
            for c in o["cons"]:
                st.markdown(f"- {c}")
        with st.expander("Why this score? Cost and assumptions"):
            st.write({LABELS[k]: round(v, 1) for k, v in o["scores"].items()})
            for r in o["reasons"]:
                st.markdown(f"- {r['reason']}  *(effect: {', '.join(f'{LABELS[k]} {v:+g}' for k, v in r['effects'].items())})*")
            for n in est.get("notes", []):
                st.caption(n)
    charts.show(charts.criteria_chart(options, LABELS))


def decision_box(title, options):
    """Record the owner's choice without treating the system ranking as an automatic decision."""
    store = st.session_state.setdefault("decisions", {})
    names = ["Not decided yet"] + [o["name"] for o in options]
    cur = store.get(title, "Not decided yet")
    choice = st.selectbox("My decision", names, index=names.index(cur) if cur in names else 0, key=f"dec_{title}")
    store[title] = choice
    st.caption("You choose the final action. BizSage compares the options; its ranking is guidance, not a decision.")


def problem_tab(pid, s):
    """Score and compare alternatives for one decision problem using the current findings."""
    problem = next(p for p in kb.strategies["problems"] if p["id"] == pid)
    relevant = pid in dss.relevant_problems(kb, s.state["hypotheses"])
    html(f'<div class="bs-card"><h4>{esc(problem["question"])} {badge("Findings point here" if relevant else "Not a priority from the findings", "success" if relevant else "neutral")}</h4></div>')
    ctx = dss.build_context(s.state, s.state["hypotheses"])
    options = dss.score_problem(kb, pid, ctx, weights(), assumptions())
    option_cards(options, problem["title"])
    decision_box(problem["title"], options)


def _controls():
    """Expose DSS preferences while clearly distinguishing assumptions from known facts."""
    w = weights()
    with st.expander("Scoring weights (how much each criterion matters to you)"):
        cols = st.columns(len(w))
        for col, c in zip(cols, kb.strategies["criteria"]):
            w[c["id"]] = col.slider(c["label"], 0, 100, int(round(w[c["id"]] * 100)), key=f"w_{c['id']}") / 100
        st.caption("Weights are normalised automatically. Changing them re-ranks the options instantly.")
    a = assumptions()
    with st.expander("Assumptions behind the estimates (editable)"):
        cols = st.columns(2)
        for i, (k, v) in enumerate(list(a.items())):
            a[k] = cols[i % 2].number_input(ASSUMP_LABELS.get(k, k), value=float(v), key=f"as_{k}")
        st.caption("These are illustrative assumptions, not measured facts. Adjust them to match your restaurant.")


def _branch_defaults():
    """Return the included Demo Data branch-chain example."""
    return CASES["branches"]


def branch_tab(s):
    """Collect branch history and present comparison signals plus owner-controlled options."""
    html('<div class="bs-card"><h4>Should the weakest branch stay open?</h4><p>Compare branches by trend and efficiency, check whether they move together (competing for the same customers), '
         'and whether a branch follows the same pattern as an older reference branch. BizSage then lays out the options; you decide.</p></div>')
    data = st.session_state.get("branch_data")
    c1, c2 = st.columns([1, 3])
    if c1.button("Load sample chain", key="load_branches"):
        st.session_state["branch_data"] = {"branches": [dict(b) for b in _branch_defaults()["branches"]], "reference": _branch_defaults()["reference"]}
        for k in list(st.session_state.keys()):
            if k.startswith(("be_", "bn_")):
                del st.session_state[k]
        st.rerun()
    if not data:
        c2.info("Load the sample chain (Demo Data) or build your own with the boxes below.")
        data = {"branches": [{"name": f"Branch {i + 1}", "seats": 0, "staff": 0, "revenue": [None] * 6, "expenses": [None] * 6, "customers": [None] * 6} for i in range(2)], "reference": ""}
    n = st.selectbox("Number of branches", [2, 3, 4], index=min(max(len(data["branches"]), 2), 4) - 2)
    branches_in = []
    for i in range(n):
        b = data["branches"][i] if i < len(data["branches"]) else {"name": f"Branch {i + 1}", "seats": 0, "staff": 0, "revenue": [None] * 6, "expenses": [None] * 6, "customers": [None] * 6}
        with st.expander(f"Branch {i + 1}: {b['name']}", expanded=(i == 0 and not st.session_state.get("branch_data"))):
            a, bb, cc = st.columns(3)
            name = a.text_input("Name", value=b["name"], key=f"bn_name_{i}")
            seats = bb.number_input("Seats", 0, 5000, int(b.get("seats") or 0), key=f"bn_seats_{i}")
            staff = cc.number_input("Staff", 0, 500, int(b.get("staff") or 0), key=f"bn_staff_{i}")
            df = pd.DataFrame({"Month": list(range(1, 7)), "Revenue (Rs)": b["revenue"], "Expenses (Rs)": b["expenses"], "Customers": b["customers"]})
            ed = st.data_editor(df, hide_index=True, num_rows="fixed", key=f"be_{i}", width="stretch",
                                column_config={"Month": st.column_config.NumberColumn(disabled=True)})
            conv = lambda col: [None if pd.isna(x) else float(x) for x in ed[col]]
            branches_in.append({"name": name or f"Branch {i + 1}", "seats": seats, "staff": staff, "revenue": conv("Revenue (Rs)"),
                                "expenses": conv("Expenses (Rs)"), "customers": conv("Customers")})
    names = [b["name"] for b in branches_in]
    ref_default = data.get("reference") if data.get("reference") in names else names[0]
    reference = st.selectbox("Reference branch (the older branch to compare against)", names, index=names.index(ref_default))
    if st.button("Analyse branches", type="primary", key="run_branches"):
        st.session_state["branch_result"] = br.analyze(kb, branches_in, reference, weights(), assumptions(), s.state["facts"].get("delivery_declining"),
                                                         s.state["derived"].get("food_cost_ratio"))
        st.session_state["branch_inputs"] = branches_in
    res = st.session_state.get("branch_result")
    if not res:
        return
    inputs = st.session_state["branch_inputs"]
    charts.show(charts.branch_lines(inputs))
    rows = [{"Branch": m["name"], "Margin (%)": None if m["margin_pct"] is None else round(m["margin_pct"], 1),
             "Trend (% per month)": None if m["slope_pct"] is None else round(m["slope_pct"], 1),
             "Revenue per staff (Rs)": None if m["rev_per_staff"] is None else round(m["rev_per_staff"]), "Health": m["health"]} for m in res["metrics"]]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    c1, c2 = st.columns(2)
    with c1:
        charts.show(charts.corr_heatmap(res["correlation"]))
    with c2:
        for t in res["together"]:
            html(f'<div class="bs-card"><h4>{esc(t["a"])} and {esc(t["b"])} move together {badge("similarity " + format(t["corr"], ".2f"), "info")}</h4>'
                 f'<p>{"Both are declining at the same time. They may be competing for the same customers, or hit by the same market change." if t["declining_together"] else "Their sales follow almost the same pattern."}</p></div>')
        for r in res["reference"]:
            html(f'<div class="bs-card"><h4>{esc(r["verdict"])}</h4><p>Pattern similarity: {"n/a" if r["corr"] is None else format(r["corr"], ".2f")}</p></div>')
    if res["weakest"]:
        note(f"The weakest branch by profit margin is <b>{esc(res['weakest']['name'])}</b> ({res['weakest']['margin_pct']:.1f}% margin).", "Finding")
        option_cards(res["options"], "Branch decision")
        decision_box("Branch decision", res["options"])


def render(show_header=True):
    if show_header:
        header("Decision support centre", "BizSage lays out the alternatives with scores, advantages, disadvantages and estimates. It does not decide. The decision is yours.")
    require_data()
    s = rs()
    note("Scores are a transparent weighted comparison, not a prediction. Change the weights or assumptions below and watch the ranking change.", "How to read this")
    _controls()
    tabs = st.tabs(["Staffing strategy", "Cost and margin", "Cash-flow recovery", "Branch and franchise"])
    with tabs[0]:
        problem_tab("staffing", s)
    with tabs[1]:
        problem_tab("margin", s)
    with tabs[2]:
        problem_tab("cash", s)
    with tabs[3]:
        branch_tab(s)
