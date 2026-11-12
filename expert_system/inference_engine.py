"""Forward-chaining inference engine.

Cycle: match every rule against Working Memory -> fire the rules whose conditions are TRUE -> rules may ASSERT new facts
-> repeat until nothing new can be concluded (a fixed point) or MAX_CYCLES is reached (safe termination).
Rules that depend on a fact concluded by another rule (chained rules) fire in a later cycle."""
from dataclasses import dataclass, field
from typing import Dict, List

from expert_system.knowledge_loader import KnowledgeBase
from expert_system.rule_interpreter import FALSE, TRUE, UNKNOWN, evaluate_rule, format_text
from expert_system.working_memory import WorkingMemory

MAX_CYCLES = 10


@dataclass
class Firing:
    rule_id: str
    rule_name: str
    kind: str
    cycle: int
    certainty: float                 # min certainty of the facts used (1.0 = exact data)
    effects: List[dict]              # [{hypothesis, cf (signed, already multiplied by certainty), base_cf, group}]
    explanation: str
    facts_used: Dict[str, object]
    next_question: str = None


@dataclass
class InferenceResult:
    firings: List[Firing] = field(default_factory=list)
    rule_status: Dict[str, str] = field(default_factory=dict)
    unknown_facts: Dict[str, List[str]] = field(default_factory=dict)   # rule id -> facts missing
    asserted: Dict[str, object] = field(default_factory=dict)
    cycles: int = 0
    memory: WorkingMemory = None     # working memory including asserted facts

    def fired_ids(self):
        return [f.rule_id for f in self.firings]

    def counts(self):
        c = {TRUE: 0, FALSE: 0, UNKNOWN: 0}
        for s in self.rule_status.values():
            c[s] += 1
        return c


def run(kb: KnowledgeBase, wm: WorkingMemory) -> InferenceResult:
    """Run rules to a fixed point without modifying the caller's original working memory."""
    work = wm.copy()
    result = InferenceResult()
    fired = set()
    for cycle in range(1, MAX_CYCLES + 1):
        # Evaluate against one stable snapshot; conclusions from this pass become visible next cycle.
        newly = []
        for rule in kb.rules:
            if rule["id"] in fired:
                continue
            ev = evaluate_rule(rule, work)
            if ev.status != TRUE:
                continue
            cert = min([f.certainty for f in ev.used.values()] or [1.0])
            effects = [{"hypothesis": e["hypothesis"], "cf": round(e["cf"] * cert, 4), "base_cf": e["cf"], "group": e.get("group")}
                       for e in rule["effects"]]
            text = format_text(rule["explanation"], {k: f.value for k, f in ev.used.items()}, kb.thresholds)
            result.firings.append(Firing(rule["id"], rule["name"], rule["kind"], cycle, cert, effects, text,
                                         {k: f.value for k, f in ev.used.items()}, rule.get("next_question")))
            fired.add(rule["id"])
            newly.append((rule, cert))
        # Chaining is explicit: asserted facts can enable another rule on the following pass.
        for rule, cert in newly:
            for a in rule.get("asserts", []):
                if not work.has(a["fact"]):
                    work.set(a["fact"], a["value"], cert, f"asserted:{rule['id']}")
                    result.asserted[a["fact"]] = a["value"]
        result.cycles = cycle
        if not newly:
            break
    for rule in kb.rules:                      # final status of every rule, for explanations and question selection
        if rule["id"] in fired:
            result.rule_status[rule["id"]] = TRUE
        else:
            ev = evaluate_rule(rule, work)
            result.rule_status[rule["id"]] = ev.status
            result.unknown_facts[rule["id"]] = ev.unknown_facts
    result.memory = work
    return result
