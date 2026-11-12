"""Data-quality subsystem: validation, missing data, contradictions and redundancy. The system never crashes on bad data."""
from dataclasses import dataclass
from typing import Dict, List, Tuple

from expert_system.knowledge_loader import KnowledgeBase
from expert_system.rule_interpreter import TRUE, evaluate_rule, format_text
from expert_system.working_memory import WorkingMemory


@dataclass
class Issue:
    severity: str      # error | warning | info | conflict
    field: str
    message: str


def _is_num(x):
    """Reject booleans as numeric data even though Python treats bool as an int subtype."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_inputs(kb: KnowledgeBase, raw: dict, history: List[dict]) -> Tuple[dict, List[dict], List[Issue]]:
    """Returns cleaned copies (invalid values removed, i.e. treated as UNKNOWN) and a list of issues."""
    issues: List[Issue] = []
    # Invalid or out-of-range values are omitted so later rules see UNKNOWN, not a guessed value.
    clean = {}
    for k, v in raw.items():
        spec = kb.inputs.get(k)
        if v is None or spec is None:
            continue
        if not _is_num(v):
            issues.append(Issue("error", k, f"'{spec['label']}' must be a number. It was ignored (treated as unknown)."))
            continue
        if v < spec["min"] or v > spec["max"]:
            issues.append(Issue("error", k, f"'{spec['label']}' ({v:,.0f}) is outside the valid range and was ignored (treated as unknown)."))
            continue
        clean[k] = float(v)
    if "wastage_pct" in clean and clean["wastage_pct"] > 60:
        issues.append(Issue("warning", "wastage_pct", "Wastage above 60% is unusual. Please confirm it."))
    cleaned_hist, gaps = [], 0
    for i, row in enumerate(history):
        r = {}
        for key in ("revenue", "expenses", "customers", "food_cost"):
            v = row.get(key)
            if v is None:
                gaps += 1
                continue
            if not _is_num(v) or v < 0:
                issues.append(Issue("error", f"history[{i + 1}].{key}", f"Month {i + 1} {key.replace('_', ' ')} is invalid (negative or not a number) and was ignored."))
                continue
            r[key] = float(v)
        cleaned_hist.append(r)
    for i in range(1, len(cleaned_hist)):
        a, b = cleaned_hist[i - 1].get("revenue"), cleaned_hist[i].get("revenue")
        if a and b and (b > 1.8 * a or b < 0.2 * a):
            issues.append(Issue("warning", f"history[{i + 1}].revenue", f"Revenue changed by more than 80% between month {i} and month {i + 1}. Please confirm the figures."))
    c = cleaned_hist[-1] if cleaned_hist else {}
    if c.get("revenue") == 0:
        issues.append(Issue("error", "history", "Current-month revenue is zero, so ratios that divide by revenue are unavailable."))
    if c.get("customers") == 0 and c.get("revenue"):
        issues.append(Issue("warning", "history", "Customers are zero but revenue is positive. Please check."))
    filled = sum(1 for r in cleaned_hist if r.get("revenue") is not None)
    if filled < 3:
        issues.append(Issue("info", "history", f"Only {filled} month(s) of revenue history. Trend rules need at least 4 months to work fully."))
    if gaps:
        issues.append(Issue("info", "history", f"{gaps} blank cell(s) in the monthly history. Rules that need them will be skipped, not guessed."))
    return clean, cleaned_hist, issues


def check_consistency(kb: KnowledgeBase, wm: WorkingMemory) -> List[dict]:
    """Declarative consistency checks (same interpreter as the rules). Conflicts dispute the answers involved."""
    found = []
    for ck in kb.consistency:
        ev = evaluate_rule(ck, wm)
        if ev.status == TRUE:
            text = format_text(ck["message"], {k: f.value for k, f in ev.used.items()}, kb.thresholds)
            found.append({"id": ck["id"], "severity": ck["severity"], "message": text, "disputes": ck["disputes"]})
    return found


def missing_summary(kb: KnowledgeBase, raw_clean: dict, history_clean: List[dict]) -> dict:
    """Report completeness by input group and list missing labels; this does not impute values."""
    spec_required = [k for k, v in kb.inputs.items() if not v.get("optional")]
    provided_required = [k for k in spec_required if k in raw_clean]
    optional = [k for k, v in kb.inputs.items() if v.get("optional")]
    provided_opt = [k for k in optional if k in raw_clean]
    cells = sum(1 for r in history_clean for k in ("revenue", "expenses", "customers", "food_cost") if r.get(k) is not None)
    total_cells = max(1, len(history_clean) * 4)
    parts = [len(provided_required) / max(1, len(spec_required)), len(provided_opt) / max(1, len(optional)), cells / total_cells]
    return {"completeness_pct": round(100 * (0.5 * parts[0] + 0.2 * parts[1] + 0.3 * parts[2])),
            "missing_required": [kb.inputs[k]["label"] for k in spec_required if k not in raw_clean],
            "missing_optional": [kb.inputs[k]["label"] for k in optional if k not in raw_clean]}
