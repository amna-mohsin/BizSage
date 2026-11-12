"""Question Selector: asks the question whose answer would teach the system the MOST about the hypotheses that are
still undecided. The next question therefore changes as the evidence changes."""
from typing import Dict, List

from config import MIN_QUESTIONS_TO_VIEW_RESULTS
from expert_system.hypothesis_manager import HypothesisResult
from expert_system.inference_engine import InferenceResult
from expert_system.knowledge_loader import KnowledgeBase
from expert_system.rule_interpreter import UNKNOWN
from expert_system.working_memory import WorkingMemory


def _uncertainty(h: HypothesisResult, cf: float) -> float:
    """Estimate how much room remains for an answer to change a hypothesis."""
    if h.net is None:
        return 0.8
    u = 1 - abs(h.net)
    if h.ruled_out and cf > 0:
        u *= 0.2
    if h.net >= 0.9:
        u *= 0.25
    return u


def rank_questions(kb: KnowledgeBase, wm: WorkingMemory, res: InferenceResult, hyps: Dict[str, HypothesisResult],
                   asked: set, followups: set) -> List[dict]:
    """Rank unanswered facts by expected influence on unresolved findings."""
    askable = kb.askable_facts()
    scores: Dict[str, dict] = {}
    for rule in kb.rules:
        if res.rule_status.get(rule["id"]) != UNKNOWN:
            continue
        missing = []
        for m in res.unknown_facts.get(rule["id"], []):
            missing.extend(kb.facts[m].get("ask_via", [m]))
        for fid in missing:
            if fid not in askable or fid in asked or wm.has(fid) or fid in wm.dont_know or wm.is_disputed(fid):
                continue
            # A question that is only one of several missing conditions is less immediately useful.
            readiness = 1.0 / len(missing)
            gain = sum(abs(e["cf"]) * _uncertainty(hyps[e["hypothesis"]], e["cf"]) for e in rule["effects"]) * readiness
            slot = scores.setdefault(fid, {"fact": fid, "score": 0.0, "hyps": set(), "rules": []})
            slot["score"] += gain
            slot["hyps"].update(e["hypothesis"] for e in rule["effects"])
            slot["rules"].append(rule["id"])
    # Keep the minimum-answer requirement reachable if no currently unresolved rule
    # has a question left: ask an unanswered input that still appears in the rule base.
    if not scores and len(asked) < MIN_QUESTIONS_TO_VIEW_RESULTS:
        for rule in kb.rules:
            for condition in rule["conditions"]:
                for fid in kb.facts[condition["fact"]].get("ask_via", [condition["fact"]]):
                    if fid not in askable or fid in asked or wm.has(fid) or wm.is_disputed(fid):
                        continue
                    slot = scores.setdefault(
                        fid,
                        {"fact": fid, "score": 0.0, "hyps": set(), "rules": [], "minimum_only": True},
                    )
                    slot["score"] += sum(abs(e["cf"]) for e in rule["effects"]) / len(rule["conditions"])
                    slot["hyps"].update(e["hypothesis"] for e in rule["effects"])
                    slot["rules"].append(rule["id"])
    out = []
    for fid, s in scores.items():
        # Prefer questions that inform multiple causes; chained rules can also nominate follow-ups.
        score = s["score"] * (1.15 if len(s["hyps"]) >= 2 else 1.0) + (0.5 if fid in followups else 0.0)
        names = [hyps[h].name for h in sorted(s["hyps"], key=lambda h: -(hyps[h].net or 0))][:3]
        reason = (
            "To complete the minimum assessment, this related factor may add context about: "
            + "; ".join(names) + ". It may not change the current findings."
            if s.get("minimum_only")
            else "The answer can strengthen or weaken: " + "; ".join(names) + "."
        )
        out.append({"fact": fid, "score": round(score, 4), "rules": sorted(set(s["rules"])), "hypotheses": sorted(s["hyps"]),
                    "reason": reason})
    return sorted(out, key=lambda q: (-q["score"], q["fact"]))
