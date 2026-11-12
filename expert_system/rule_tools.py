"""Build readable examples for explaining declarative rule conditions during demonstrations."""
from expert_system.working_memory import WorkingMemory


def satisfying_value(c: dict):
    """Choose one representative value that satisfies a supported comparison operator."""
    op, t = c["op"], c.get("target")
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


def example_facts(rule: dict) -> WorkingMemory:
    """Create working memory containing a satisfying value for every rule condition."""
    wm = WorkingMemory()
    for c in rule["conditions"]:
        wm.set(c["fact"], satisfying_value(c))
    return wm


def describe_condition(c: dict, facts: dict) -> str:
    """Translate the machine-readable condition into a plain-language sentence."""
    label = facts[c["fact"]]["label"]
    t = c.get("target")
    words = {"lt": "is below", "le": "is at most", "gt": "is above", "ge": "is at least", "eq": "equals", "ne": "is not",
             "between": "is between", "in": "is one of", "true": "is YES", "false": "is NO"}[c["op"]]
    if c["op"] in ("true", "false"):
        return f"{label} {words}"
    shown = ", ".join(map(str, t)) if isinstance(t, list) else (f"{t:g}" if isinstance(t, (int, float)) else str(t))
    raw = c.get("value")
    ref = f"  (threshold: {raw})" if isinstance(raw, str) and raw.lstrip("-").startswith("$") else ""
    return f"{label} {words} {shown}{ref}"
