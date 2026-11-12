"""Proves the Knowledge Base requirements: 50+ unique conditions, declarative schema, nothing dangling."""
from expert_system.knowledge_loader import load_kb

kb = load_kb()


def test_kb_validates_without_errors():
    assert kb.validate() == []


def test_at_least_50_unique_diagnostic_conditions():
    rules = kb.diagnostic_rules
    assert len(rules) >= 50
    assert len({kb.signature(r) for r in rules}) == len(rules), "two diagnostic rules share identical conditions"


def test_ten_conditions_in_each_of_six_categories():
    cats = kb.stats()["diagnostic_by_category"]
    assert len(cats) == 6 and all(n == 10 for n in cats.values())


def test_every_hypothesis_has_supporting_and_some_rule_evidence():
    pos = {e["hypothesis"] for r in kb.rules for e in r["effects"] if e["cf"] > 0}
    assert pos == set(kb.hypotheses)


def test_exclusion_rules_have_negative_effects_only():
    for r in kb.rules:
        if r["kind"] == "exclusion":
            assert all(e["cf"] < 0 for e in r["effects"])
        else:
            assert all(e["cf"] > 0 for e in r["effects"])


def test_every_rule_has_explanation_and_declarative_fields():
    for r in kb.rules:
        assert r["explanation"] and r["name"] and r["conditions"] and r["effects"], r["id"]


def test_every_askable_fact_is_used_by_a_rule_or_check():
    used = {c["fact"] for r in kb.rules + kb.consistency for c in r["conditions"]}
    used |= {a for f in kb.facts.values() for a in f.get("ask_via", [])}
    for fid in kb.askable_facts():
        assert fid in used, f"question '{fid}' is never used"


def test_thresholds_live_in_one_editable_file():
    for r in kb.rules:
        for c in r["conditions"]:
            if isinstance(c.get("value"), str) and c["value"].lstrip("-").startswith("$"):
                assert c["target"] is not None
