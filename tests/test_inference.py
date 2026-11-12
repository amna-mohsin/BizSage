"""Behaviour of the expert system: the reasoning loop, uncertainty, elimination, missing/contradictory/redundant data."""
from expert_system import hypothesis_manager, inference_engine
from expert_system.knowledge_loader import load_kb
from expert_system.reasoning_controller import ReasoningSession
from expert_system.working_memory import WorkingMemory
from tests.helpers import case_session, empty_session

kb = load_kb()


def net(s, hid):
    return s.state["hypotheses"][hid].net


def test_multiple_hypotheses_coexist():
    s = case_session()
    active = [h for h in s.state["hypotheses"].values() if h.net is not None and h.net >= 0.4]
    assert len(active) >= 4


def test_forward_chaining_reaches_a_second_cycle():
    wm = WorkingMemory()
    wm.set("cash_buffer_months", 0.5)
    wm.set("expansion_financed_by_debt", True)
    res = inference_engine.run(kb, wm)
    cycles = {f.rule_id: f.cycle for f in res.firings}
    assert cycles["R21"] == 1 and cycles["R60"] == 2 and "cash_stress" in res.asserted


def test_engine_terminates_and_reports_cycles():
    res = inference_engine.run(kb, case_session().state["wm"])
    assert 1 <= res.cycles <= inference_engine.MAX_CYCLES


def test_new_evidence_updates_and_can_eliminate_a_hypothesis():
    s = case_session()
    before = net(s, "H_FOODCOST")
    s.answer("supplier_prices_up", False, 1.0, "No, definitely not")
    after = net(s, "H_FOODCOST")
    assert after < before
    assert s.state["hypotheses"]["H_FOODCOST"].label in ("Possible (maybe)", "Weak signal (not sure)", "Weakened (unlikely)", "Not enough evidence")


def test_contradicting_evidence_rules_out_a_hypothesis():
    s = empty_session()
    s.set_inputs({"wastage_pct": 2}, s.history, {})
    s.analyze()
    assert s.state["hypotheses"]["H_WASTAGE"].ruled_out


def test_dont_know_is_not_treated_as_no():
    s = case_session()
    s.answer("supplier_prices_up", None, 1.0, "Not sure")
    assert "supplier_prices_up" not in s.state["facts"]
    assert "X01" not in s.state["result"].fired_ids()
    assert s.state["result"].rule_status["X01"] != "TRUE"


def test_probably_answers_carry_lower_certainty():
    a, b = case_session(), case_session()
    a.answer("idle_time", True, 1.0, "Yes, definitely")
    b.answer("idle_time", True, 0.7, "Probably yes")
    assert net(b, "H_LABOUR") <= net(a, "H_LABOUR")
    ea = [e for e in a.state["hypotheses"]["H_LABOUR"].evidence_for if e.rule_id == "R48"][0]
    eb = [e for e in b.state["hypotheses"]["H_LABOUR"].evidence_for if e.rule_id == "R48"][0]
    assert abs(eb.cf) < abs(ea.cf)


def test_word_answers_are_accepted_with_lower_certainty():
    s = case_session()
    s.set_inputs({k: v for k, v in s.raw.items() if k != "wastage_pct"}, s.history, s.profile)
    s.analyze()
    s.answer("wastage_pct", 16.0, 0.8, "high")
    assert s.state["facts"]["wastage_pct"] == 16.0
    assert s.state["wm"].get("wastage_pct").certainty == 0.8


def test_redundant_evidence_is_consolidated_not_double_counted():
    s = case_session()
    labour = s.state["hypotheses"]["H_LABOUR"]
    consolidated = [e for e in labour.evidence_for if e.consolidated]
    assert consolidated and all(e.weight < 1 for e in consolidated)
    assert labour.redundant


def test_inconclusive_when_there_is_no_evidence():
    s = empty_session()
    assert s.state["conclusion"]["inconclusive"] and s.state["conclusion"]["primary"] is None
    assert "Insufficient evidence" in s.summary_text()


def test_missing_data_does_not_stop_unrelated_reasoning():
    s = case_session()
    s.set_inputs({k: v for k, v in s.raw.items() if k not in ("inventory_value", "equity", "total_debt")}, s.history, s.profile)
    st = s.analyze()
    assert "inventory_days" not in st["derived"] and "debt_to_equity" not in st["derived"]
    assert st["hypotheses"]["H_LABOUR"].net is not None


def test_invalid_input_is_ignored_and_reported():
    s = case_session()
    s.set_inputs({**s.raw, "wastage_pct": -5, "rent": "abc"}, s.history, s.profile)
    st = s.analyze()
    assert any(i.severity == "error" for i in st["issues"]) and "wastage_pct" not in st["facts"]


def test_zero_denominator_makes_metric_unavailable():
    s = case_session()
    h = [dict(r) for r in s.history]
    h[-1]["revenue"] = 0
    s.set_inputs(s.raw, h, s.profile)
    st = s.analyze()
    assert "food_cost_ratio" not in st["derived"] and "labour_cost_ratio" not in st["derived"]


def test_contradictory_profit_is_flagged():
    s = case_session()
    s.set_inputs({**s.raw, "reported_net_profit": 150000}, s.history, s.profile)
    st = s.analyze()
    assert any(c["id"] == "CK07" for c in st["conflicts"])


def test_conflicting_answer_pauses_rules_until_confirmed():
    s = case_session()
    h = [dict(r) for r in s.history]
    h[-1]["customers"] = 2000                                       # a 30% fall in customer visits
    s.set_inputs(s.raw, h, s.profile)
    s.analyze()
    s.answer("orders_trend", "increasing", 1.0, "increasing")      # customers fell, so this conflicts
    assert "orders_trend" in s.state["clarify"]
    assert s.current_question()["type"] == "clarify"
    s.answer("orders_trend", "decreasing", 1.0, "decreasing")       # corrected answer
    assert "orders_trend" not in s.state["clarify"] and "R04" in s.state["result"].fired_ids()
    s.answer("repeat_trend", "increasing", 1.0, "increasing")
    if "repeat_trend" in s.state["clarify"]:
        s.confirm("repeat_trend")
        assert "repeat_trend" not in s.state["clarify"]


def test_next_question_changes_as_evidence_changes():
    s = case_session()
    first = s.current_question()["fact"]
    s.answer(first, None, 1.0, "Not sure")
    second = s.current_question()["fact"]
    assert first != second
    asked = {first}
    for _ in range(3):
        q = s.current_question()
        assert q["fact"] not in asked
        asked.add(q["fact"])
        s.answer(q["fact"], None, 1.0, "Not sure")


def test_questions_target_unresolved_hypotheses():
    s = case_session()
    q = s.current_question()
    assert q["hypotheses"] and q["score"] > 0 and "why" in q


def test_loop_terminates_safely():
    s = case_session()
    steps = 0
    while s.current_question() is not None and steps < 200:
        q = s.current_question()
        s.answer(q["fact"], None, 1.0, "Not sure")
        steps += 1
    assert steps <= 200 and s.termination() is not None


def test_timeline_records_changes_after_each_answer():
    s = case_session()
    s.answer("repeat_trend", "decreasing", 1.0, "decreasing")
    assert s.steps and s.steps[-1]["changes"]


def test_session_export_and_load_roundtrip():
    s = case_session()
    s.answer("idle_time", True, 1.0, "Yes, definitely")
    t = ReasoningSession()
    t.load_state(s.export_state())
    assert abs(t.state["hypotheses"]["H_LABOUR"].score - s.state["hypotheses"]["H_LABOUR"].score) < 1e-9


def test_certainty_never_reaches_one_and_bands_work():
    from expert_system.certainty import combine, label_for
    assert combine([0.9, 0.9, 0.9]) < 1
    assert label_for(0.97)[0] == "Definitely" and label_for(0.8)[0] == "Quite possible" and label_for(-0.6)[0] == "Ruled out"


def test_follow_up_question_depends_on_the_previous_answer():
    """Answer 'same food every day' -> investigate unsold food; answer 'no' -> investigate other causes of wastage."""
    yes, no = case_session(), case_session()
    yes.answer("prep_same_weekday_weekend", True, 1.0, "Yes, definitely")
    no.answer("prep_same_weekday_weekend", False, 1.0, "No, definitely not")
    yes_next = [q["fact"] for q in yes.state["ranked_questions"][:4]]
    no_next = [q["fact"] for q in no.state["ranked_questions"][:4]]
    assert "unsold_food" in yes_next and "expiry_before_use" not in yes_next
    assert "expiry_before_use" in no_next and "unsold_food" not in no_next
