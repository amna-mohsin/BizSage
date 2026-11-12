"""Loads the declarative Knowledge Base (JSON) and validates it. Adding a rule = adding JSON, no code change."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
RULE_FILES = ["revenue_rules.json", "expense_rules.json", "cashflow_rules.json", "inventory_rules.json",
              "staffing_rules.json", "stability_rules.json", "exclusion_rules.json", "chained_rules.json"]
OPERATORS = {"lt", "le", "gt", "ge", "eq", "ne", "between", "in", "true", "false"}


def _read(name: str):
    """Read one UTF-8 knowledge-base document from the project data directory."""
    return json.loads((KB_DIR / name).read_text(encoding="utf-8"))


def resolve(value, thresholds: dict):
    """Replaces '$name' (and '-$name') by the named threshold, so numbers live in one editable file."""
    if isinstance(value, str) and value.startswith("-$"):
        return -thresholds[value[2:]]
    if isinstance(value, str) and value.startswith("$"):
        return thresholds[value[1:]]
    if isinstance(value, list):
        return [resolve(v, thresholds) for v in value]
    return value


class KnowledgeBase:
    def __init__(self):
        """Load the domain data, resolve named thresholds, and index all rules."""
        self.facts: Dict[str, dict] = _read("facts.json")
        self.inputs: Dict[str, dict] = _read("inputs.json")
        self.thresholds: dict = {k: v for k, v in _read("thresholds.json").items() if not k.startswith("_")}
        self.hypotheses: Dict[str, dict] = _read("hypotheses.json")
        self.consistency: List[dict] = _read("consistency_checks.json")
        self.strategies: dict = _read("strategies.json")
        self.rules: List[dict] = []
        for f in RULE_FILES:
            self.rules.extend(_read(f))
        for item in self.rules + self.consistency:
            for c in item["conditions"]:
                c["target"] = resolve(c.get("value"), self.thresholds)
        self.rules_by_id = {r["id"]: r for r in self.rules}

    @property
    def diagnostic_rules(self):
        return [r for r in self.rules if r["kind"] == "diagnostic"]

    def askable_facts(self):
        return {fid: f for fid, f in self.facts.items() if f.get("askable")}

    def stats(self) -> dict:
        kinds = {}
        for r in self.rules:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        cats = {}
        for r in self.diagnostic_rules:
            cats[r["category"]] = cats.get(r["category"], 0) + 1
        return {"total_rules": len(self.rules), "by_kind": kinds, "diagnostic_by_category": cats,
                "hypotheses": len(self.hypotheses), "facts": len(self.facts), "questions": len(self.askable_facts()),
                "consistency_checks": len(self.consistency)}

    @staticmethod
    def signature(rule: dict):
        return tuple(sorted((c["fact"], c["op"], json.dumps(c.get("value"))) for c in rule["conditions"]))

    def validate(self) -> List[str]:
        """Return schema/reference errors before the engine relies on any rule."""
        errors, seen_ids, seen_sig = [], set(), {}
        for r in self.rules:
            if r["id"] in seen_ids:
                errors.append(f"{r['id']}: duplicate rule id")
            seen_ids.add(r["id"])
            for c in r["conditions"]:
                if c["fact"] not in self.facts:
                    errors.append(f"{r['id']}: unknown fact '{c['fact']}'")
                if c["op"] not in OPERATORS:
                    errors.append(f"{r['id']}: unknown operator '{c['op']}'")
            for e in r["effects"]:
                if e["hypothesis"] not in self.hypotheses:
                    errors.append(f"{r['id']}: unknown hypothesis '{e['hypothesis']}'")
                if not -1 <= e["cf"] <= 1:
                    errors.append(f"{r['id']}: certainty factor out of range")
            for a in r.get("asserts", []):
                if a["fact"] not in self.facts:
                    errors.append(f"{r['id']}: asserts unknown fact '{a['fact']}'")
            if r.get("next_question") and r["next_question"] not in self.facts:
                errors.append(f"{r['id']}: unknown next_question")
            if r["kind"] == "diagnostic":
                sig = self.signature(r)
                if sig in seen_sig:
                    errors.append(f"{r['id']}: same condition as {seen_sig[sig]} (not a unique condition)")
                seen_sig[sig] = r["id"]
        for ck in self.consistency:
            for c in ck["conditions"]:
                if c["fact"] not in self.facts:
                    errors.append(f"{ck['id']}: unknown fact '{c['fact']}'")
        return errors


@lru_cache(maxsize=1)
def load_kb() -> KnowledgeBase:
    return KnowledgeBase()
