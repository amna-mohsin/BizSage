"""Branch / franchise comparison (the 'should this branch stay open?' decision).
Compares trends and efficiency across branches, checks whether branches move together (competing for the same customers)
and whether a branch follows the same pattern as an older reference branch, then lays out the options with pros and cons."""
from typing import Dict, List, Optional

import numpy as np

from decision_support import dss
from expert_system.knowledge_loader import KnowledgeBase


def _clean(xs):
    """Drop unavailable observations before calculating a trend or correlation."""
    return [float(x) for x in xs if x is not None]


def _slope_pct(series: List[Optional[float]]) -> Optional[float]:
    """Express the fitted monthly trend as a percentage of the average branch revenue."""
    ys = _clean(series)
    if len(ys) < 3 or np.mean(ys) == 0:
        return None
    xs = np.arange(len(ys))
    return float(np.polyfit(xs, ys, 1)[0] / np.mean(ys) * 100)


def _corr(a, b) -> Optional[float]:
    """Compare branches only on matching known months and require enough data to be meaningful."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 4:
        return None
    xa, xb = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
    if xa.std() == 0 or xb.std() == 0:
        return None
    return float(np.corrcoef(xa, xb)[0, 1])


def branch_metrics(b: dict) -> dict:
    """Summarize the latest result and trend, using 'Unknown' when evidence is incomplete."""
    rev, exp = b["revenue"], b["expenses"]
    r, e = (rev[-1] if rev else None), (exp[-1] if exp else None)
    margin = (r - e) / r * 100 if r and e is not None else None
    slope = _slope_pct(rev)
    health = "Unknown"
    if margin is not None:
        if margin < -10 or (margin < 0 and (slope or 0) < -2):
            health = "Critical"
        elif margin < 0:
            health = "Weak"
        elif margin < 8 or (slope is not None and slope < -2):
            health = "Stable"
        else:
            health = "Strong"
    return {"name": b["name"], "revenue": r, "expenses": e, "margin_pct": margin, "slope_pct": slope,
            "rev_per_staff": r / b["staff"] if r and b.get("staff") else None,
            "rev_per_seat": r / b["seats"] if r and b.get("seats") else None, "health": health}


def analyze(kb: KnowledgeBase, branches: List[dict], reference: Optional[str] = None, weights: dict = None,
            assumptions: dict = None, delivery_declining: Optional[bool] = None, food_ratio: float = None) -> dict:
    """Compare branches, flag similar/competing trends, then score options for the weakest branch."""
    metrics = [branch_metrics(b) for b in branches]
    names = [b["name"] for b in branches]
    corr = {a: {b2: _corr(branches[i]["revenue"], branches[j]["revenue"]) for j, b2 in enumerate(names)} for i, a in enumerate(names)}
    scored = [m for m in metrics if m["margin_pct"] is not None]
    weakest = min(scored, key=lambda m: m["margin_pct"]) if scored else None
    together = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            c = corr[names[i]][names[j]]
            # Strongly correlated revenue can indicate shared market demand; it is a signal, not proof.
            if c is not None and c >= 0.85:
                si, sj = metrics[i]["slope_pct"], metrics[j]["slope_pct"]
                together.append({"a": names[i], "b": names[j], "corr": c,
                                 "declining_together": si is not None and sj is not None and si <= -1 and sj <= -1})
    ref_cmp = []
    if reference and reference in names:
        ref = metrics[names.index(reference)]
        for m in metrics:
            if m["name"] == reference:
                continue
            c = corr[m["name"]][reference]
            gap = None if m["slope_pct"] is None or ref["slope_pct"] is None else m["slope_pct"] - ref["slope_pct"]
            # Similarity requires both correlated movement and a close trend slope.
            like = c is not None and c >= 0.8 and gap is not None and abs(gap) <= 2
            ref_cmp.append({"branch": m["name"], "corr": c, "slope_gap": gap,
                            "verdict": f"{m['name']} is moving like {reference}" if like else f"{m['name']} follows a different pattern from {reference}"})
    result = {"metrics": metrics, "correlation": corr, "weakest": weakest, "together": together, "reference": ref_cmp, "options": []}
    if weakest:
        ref_c = next((r["corr"] for r in ref_cmp if r["branch"] == weakest["name"]), None)
        overlap = any(t["declining_together"] and weakest["name"] in (t["a"], t["b"]) for t in together)
        wb = branches[names.index(weakest["name"])]
        cm = (1 - food_ratio / 100) if food_ratio is not None else 0.6
        facts = {"weak_margin_pct": weakest["margin_pct"], "weak_slope_pct": weakest["slope_pct"] if weakest["slope_pct"] is not None else 0.0,
                 "overlap": overlap}
        if ref_c is not None:
            facts["reference_corr"] = ref_c
        if delivery_declining is not None:
            facts["delivery_declining"] = delivery_declining
        ctx = {"facts": facts, "support": {}, "raw": {}, "latest": {},
               "branch": {"revenue": weakest["revenue"] or 0, "expenses": weakest["expenses"] or 0, "cm": cm}}
        result["options"] = dss.score_problem(kb, "branch", ctx, weights, assumptions)
        result["context"] = facts
    return result
