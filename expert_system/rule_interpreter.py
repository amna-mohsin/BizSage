"""Generic rule interpreter: reads ANY rule written in the declarative schema and evaluates it against Working Memory.
No business logic lives here; all domain knowledge is in the JSON knowledge base."""
from dataclasses import dataclass, field
from typing import Dict, List

from expert_system.working_memory import Fact, WorkingMemory

TRUE, FALSE, UNKNOWN = "TRUE", "FALSE", "UNKNOWN"


def evaluate_condition(cond: dict, wm: WorkingMemory) -> str:
    """Return TRUE/FALSE/UNKNOWN; missing or disputed facts never behave like false values."""
    fid = cond["fact"]
    fact = wm.get(fid)
    if fact is None or fact.value is None or wm.is_disputed(fid):
        return UNKNOWN
    v, op, target = fact.value, cond["op"], cond.get("target")
    try:
        if op == "true":
            return TRUE if v is True else FALSE
        if op == "false":
            return TRUE if v is False else FALSE
        if op == "in":
            return TRUE if v in target else FALSE
        if op == "eq":
            return TRUE if v == target else FALSE
        if op == "ne":
            return TRUE if v != target else FALSE
        v = float(v)
        if op == "lt": return TRUE if v < target else FALSE
        if op == "le": return TRUE if v <= target else FALSE
        if op == "gt": return TRUE if v > target else FALSE
        if op == "ge": return TRUE if v >= target else FALSE
        if op == "between": return TRUE if target[0] <= v <= target[1] else FALSE
    except (TypeError, ValueError):
        return UNKNOWN
    return UNKNOWN


@dataclass
class RuleEval:
    status: str
    used: Dict[str, Fact] = field(default_factory=dict)
    unknown_facts: List[str] = field(default_factory=list)


def evaluate_rule(rule: dict, wm: WorkingMemory) -> RuleEval:
    """TRUE if all conditions TRUE; FALSE if any condition is FALSE (even if others are unknown); otherwise UNKNOWN."""
    statuses, used, unknown = [], {}, []
    for c in rule["conditions"]:
        s = evaluate_condition(c, wm)
        statuses.append(s)
        if s == UNKNOWN:
            unknown.append(c["fact"])
        elif wm.get(c["fact"]):
            used[c["fact"]] = wm.get(c["fact"])
    # In a conjunction, one false condition is enough to reject the rule, even if others are unknown.
    if FALSE in statuses:
        return RuleEval(FALSE, used, unknown)
    if UNKNOWN in statuses:
        return RuleEval(UNKNOWN, used, unknown)
    return RuleEval(TRUE, used, unknown)


def format_text(template: str, wm_values: dict, thresholds: dict) -> str:
    """Fills {fact} and {threshold} placeholders; never raises."""
    try:
        return template.format(**{**thresholds, **wm_values})
    except Exception:
        return template
