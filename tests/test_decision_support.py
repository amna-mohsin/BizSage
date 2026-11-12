"""Regression tests for option scoring, estimates, and multi-branch recommendations."""
from decision_support import branches, dss
from expert_system.knowledge_loader import load_kb
from tests.helpers import CASES, case_session

kb = load_kb()


def ctx_for(s):
    """Build the same context shape the application passes to decision support."""
    return dss.build_context(s.state, s.state["hypotheses"])


def test_multiple_alternatives_with_pros_cons_and_scores():
    for pid in ("staffing", "margin", "cash", "branch"):
        problem = next(p for p in kb.strategies["problems"] if p["id"] == pid)
        assert len(problem["options"]) >= 4
    out = dss.score_problem(kb, "staffing", ctx_for(case_session()))
    assert len(out) == 4 and all(o["pros"] and o["cons"] and 0 <= o["weighted"] <= 100 for o in out)
    assert [o["rank"] for o in out] == [1, 2, 3, 4]


def test_scores_depend_on_findings():
    a = dss.score_problem(kb, "staffing", ctx_for(case_session()))
    b = dss.score_problem(kb, "staffing", ctx_for(case_session("lahore_cafe_cash_pressure")))
    assert {o["id"]: o["weighted"] for o in a} != {o["id"]: o["weighted"] for o in b}
    assert a[0]["id"] == "ST1"


def test_weights_are_configurable_and_normalised():
    w = dss.normalise({"financial": 3, "risk": 1, "cost": 1, "feasibility": 1, "sustainability": 0})
    assert abs(sum(w.values()) - 1) < 1e-9
    s = case_session()
    base = dss.score_problem(kb, "staffing", ctx_for(s))
    heavy = dss.score_problem(kb, "staffing", ctx_for(s), {"financial": 0, "risk": 0, "cost": 10, "feasibility": 0, "sustainability": 0})
    assert heavy[0]["id"] == "ST0" and base[0]["id"] != "ST0"       # a cost-only view prefers doing nothing


def test_assumptions_change_estimates():
    s = case_session()
    a = dss.score_problem(kb, "margin", ctx_for(s))
    b = dss.score_problem(kb, "margin", ctx_for(s), assumptions={"supplier_saving_pct": 10})
    ea = {o["id"]: o["estimate"]["monthly_net"] for o in a}["MG2"]
    eb = {o["id"]: o["estimate"]["monthly_net"] for o in b}["MG2"]
    assert eb > ea


def test_estimates_never_crash_on_missing_data():
    s = case_session()
    s.set_inputs({k: v for k, v in s.raw.items() if k != "avg_daily_wage"}, s.history, s.profile)
    s.analyze()
    out = {o["id"]: o for o in dss.score_problem(kb, "staffing", ctx_for(s))}
    assert out["ST1"]["estimate"]["available"] is False and "avg daily wage" in out["ST1"]["estimate"]["missing"][0]


def test_staffing_saving_is_capped_when_wage_is_inconsistent():
    s = case_session()
    s.set_inputs({**s.raw, "avg_daily_wage": 5000}, s.history, s.profile)
    s.analyze()
    est = {o["id"]: o for o in dss.score_problem(kb, "staffing", ctx_for(s))}["ST1"]["estimate"]
    assert est["monthly_net"] <= s.raw["labour_cost"] and any("Warning" in n for n in est["notes"])


def test_relevant_problems_follow_the_findings():
    assert "staffing" in dss.relevant_problems(kb, case_session().state["hypotheses"])
    assert "cash" in dss.relevant_problems(kb, case_session("lahore_cafe_cash_pressure").state["hypotheses"])


def test_branch_comparison_detects_competing_branches():
    c = CASES["branches"]
    r = branches.analyze(kb, c["branches"], c["reference"])
    assert r["weakest"]["name"] == "Clifton"
    assert any(t["declining_together"] for t in r["together"])
    assert r["options"][0]["id"] in ("BR1", "BR3") and len(r["options"]) == 4
    assert any("different pattern" in x["verdict"] or "moving like" in x["verdict"] for x in r["reference"])
