"""One generated test case PER RULE: build facts that satisfy the rule, then facts that break it."""
from expert_system import hypothesis_manager, inference_engine
from expert_system.knowledge_loader import load_kb
from expert_system.working_memory import WorkingMemory

kb = load_kb()


def satisfying(c):
    op, t = c["op"], c["target"]
    if op == "true": return True
    if op == "false": return False
    if op == "in": return t[0]
    if op == "eq": return t
    if op == "ne": return "other"
    if op == "lt": return t - 1
    if op == "le": return t
    if op == "gt": return t + 1
    if op == "ge": return t
    if op == "between": return (t[0] + t[1]) / 2


def violating(c):
    op, t = c["op"], c["target"]
    if op == "true": return False
    if op == "false": return True
    if op == "in": return "__not_in_list__"
    if op == "eq": return "other"
    if op == "ne": return t
    if op == "lt": return t
    if op == "le": return t + 1
    if op == "gt": return t
    if op == "ge": return t - 1
    if op == "between": return t[1] + 1


def memory(rule, break_first=False):
    wm = WorkingMemory()
    for i, c in enumerate(rule["conditions"]):
        wm.set(c["fact"], violating(c) if (break_first and i == 0) else satisfying(c))
    return wm


def test_every_rule_fires_when_its_conditions_hold_and_feeds_its_hypothesis():
    for r in kb.rules:
        res = inference_engine.run(kb, memory(r))
        assert r["id"] in res.fired_ids(), f"{r['id']} did not fire"
        hyps = hypothesis_manager.evaluate(kb, res)
        for e in r["effects"]:
            ids = [x.rule_id for x in hyps[e["hypothesis"]].evidence_for + hyps[e["hypothesis"]].evidence_against]
            assert r["id"] in ids, f"{r['id']} evidence missing for {e['hypothesis']}"


def test_every_rule_stays_silent_when_a_condition_fails():
    for r in kb.rules:
        res = inference_engine.run(kb, memory(r, break_first=True))
        assert r["id"] not in res.fired_ids(), f"{r['id']} fired although a condition was false"


def test_every_rule_is_unknown_not_false_when_data_is_missing():
    for r in kb.rules:
        res = inference_engine.run(kb, WorkingMemory())
        assert res.rule_status[r["id"]] == "UNKNOWN", r["id"]
