"""Decision Support System: lays the alternatives side by side with scores, pros, cons and estimates.
It never makes the decision; the owner does. Scoring rules are declarative (knowledge_base/strategies.json)."""
from typing import Dict, List, Optional

from decision_support.estimates import estimate
from expert_system.knowledge_loader import KnowledgeBase
from expert_system.rule_interpreter import TRUE, evaluate_condition
from expert_system.working_memory import WorkingMemory

CRITERIA_IDS = ["financial", "risk", "cost", "feasibility", "sustainability"]


def default_weights(kb: KnowledgeBase) -> Dict[str, float]:
    """Use the editable strategy knowledge base as the default criterion priorities."""
    return {c["id"]: c["weight"] for c in kb.strategies["criteria"]}


def normalise(weights: Dict[str, float]) -> Dict[str, float]:
    """Convert user-entered priorities to shares that sum to one; handle all-zero input evenly."""
    total = sum(max(w, 0) for w in weights.values())
    return {k: (max(w, 0) / total if total else 1 / len(weights)) for k, w in weights.items()}


def build_context(state: dict, hyps: dict) -> dict:
    """What the DSS knows: facts, how strongly each hypothesis is supported, and the raw figures."""
    latest = state["clean_history"][-1] if state.get("clean_history") else {}
    return {"facts": dict(state["facts"]), "support": {h: (x.net if x.net is not None else 0.0) for h, x in hyps.items()},
            "raw": dict(state["clean_raw"]), "latest": dict(latest)}


def _applies(when: dict, ctx: dict, wm: WorkingMemory) -> bool:
    """Evaluate an option modifier using either a hypothesis band or a normal rule condition."""
    if "hypothesis" in when:
        s = ctx["support"].get(when["hypothesis"], 0.0)
        return (when.get("min") is None or s >= when["min"]) and (when.get("max") is None or s <= when["max"])
    cond = {"fact": when["fact"], "op": when["op"], "target": when.get("value")}
    return evaluate_condition(cond, wm) == TRUE


def score_problem(kb: KnowledgeBase, problem_id: str, ctx: dict, weights: Optional[Dict[str, float]] = None,
                  assumptions: Optional[Dict[str, float]] = None) -> List[dict]:
    """Apply relevant score adjustments, calculate weighted rankings, and attach transparent estimates."""
    problem = next(p for p in kb.strategies["problems"] if p["id"] == problem_id)
    w = normalise(weights or default_weights(kb))
    wm = WorkingMemory()
    for k, v in ctx["facts"].items():
        wm.set(k, v)
    out = []
    for opt in problem["options"]:
        scores = dict(opt["base"])
        pros, cons, reasons = list(opt["pros"]), list(opt["cons"]), []
        # A modifier only changes scores when its stated evidence condition is satisfied.
        for m in opt["modifiers"]:
            if _applies(m["when"], ctx, wm):
                for crit, delta in m["effects"].items():
                    scores[crit] = scores[crit] + delta
                net = sum(m["effects"].values())
                # Surface the reason as a pro or con so the ranking can be explained in the UI.
                (pros if net > 0 else cons).append("Because of your data: " + m["reason"])
                reasons.append({"reason": m["reason"], "effects": m["effects"]})
        scores = {k: max(0.0, min(10.0, v)) for k, v in scores.items()}
        total = sum(w[c] * scores[c] for c in CRITERIA_IDS) * 10
        out.append({"id": opt["id"], "name": opt["name"], "summary": opt["summary"], "scores": scores, "weighted": round(total, 1),
                    "pros": pros, "cons": cons, "reasons": reasons, "estimate": estimate(opt["id"], ctx, assumptions)})
    out.sort(key=lambda o: -o["weighted"])
    for i, o in enumerate(out, 1):
        o["rank"] = i
    return out


def relevant_problems(kb: KnowledgeBase, hyps: dict) -> List[str]:
    """Which decision problems the findings point to (most supported hypotheses first)."""
    order = sorted(hyps.values(), key=lambda h: -(h.net if h.net is not None else -9))
    seen = []
    for h in order:
        if h.net is not None and h.net >= 0.15 and h.problem not in seen:
            seen.append(h.problem)
    return seen
