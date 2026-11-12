"""Hypothesis Manager: keeps ALL possible causes alive, adds support/contradiction, weakens or rules them out."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config import PRIMARY_MIN, REDUNDANT_WEIGHT
from expert_system.certainty import combine, label_for, net_certainty
from expert_system.inference_engine import InferenceResult
from expert_system.knowledge_loader import KnowledgeBase


@dataclass
class Evidence:
    rule_id: str
    rule_name: str
    cf: float
    group: Optional[str]
    explanation: str
    weight: float = 1.0
    consolidated: bool = False


@dataclass
class HypothesisResult:
    id: str
    name: str
    category: str
    investigate: str
    problem: str
    support: float = 0.0
    against: float = 0.0
    net: Optional[float] = None        # None = no evidence either way yet
    label: str = "Not yet examined"
    tone: str = "neutral"
    evidence_for: List[Evidence] = field(default_factory=list)
    evidence_against: List[Evidence] = field(default_factory=list)
    redundant: List[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.net if self.net is not None else 0.0

    @property
    def percent(self) -> int:
        return round(max(self.score, 0) * 100)

    @property
    def ruled_out(self) -> bool:
        return self.net is not None and self.net <= -0.5


def _aggregate(items: List[Evidence]):
    """Evidence in the same group measures the same thing: the strongest counts fully, the rest only partly."""
    buckets: Dict[str, List[Evidence]] = {}
    for e in items:
        buckets.setdefault(e.group or e.rule_id, []).append(e)
    weighted, notes = [], []
    # Related rules may repeat the same signal; count the strongest fully and dampen duplicates.
    for key, group in buckets.items():
        group.sort(key=lambda e: -abs(e.cf))
        for i, e in enumerate(group):
            e.weight = 1.0 if i == 0 else REDUNDANT_WEIGHT
            e.consolidated = i > 0
            weighted.append(abs(e.cf) * e.weight)
            if i > 0:
                notes.append(f"{e.rule_id} overlaps with {group[0].rule_id} (same evidence group '{key}'), counted at {int(REDUNDANT_WEIGHT * 100)}% to avoid double counting.")
    return combine(weighted), notes


def evaluate(kb: KnowledgeBase, result: InferenceResult) -> Dict[str, HypothesisResult]:
    """Collect fired-rule evidence and calculate support, contradiction, and net certainty per cause."""
    hyps = {hid: HypothesisResult(hid, h["name"], h["category"], h["investigate"], h["problem"]) for hid, h in kb.hypotheses.items()}
    for f in result.firings:
        for e in f.effects:
            ev = Evidence(f.rule_id, f.rule_name, e["cf"], e.get("group"), f.explanation)
            (hyps[e["hypothesis"]].evidence_for if e["cf"] > 0 else hyps[e["hypothesis"]].evidence_against).append(ev)
    for h in hyps.values():
        if not h.evidence_for and not h.evidence_against:
            continue
        h.support, n1 = _aggregate(h.evidence_for)
        h.against, n2 = _aggregate(h.evidence_against)
        h.redundant = n1 + n2
        h.net = round(net_certainty(h.support, h.against), 4)
        h.label, h.tone = label_for(h.net)
    return hyps


def ranked(hyps: Dict[str, HypothesisResult]) -> List[HypothesisResult]:
    """Sort supported findings first while keeping untouched hypotheses at the bottom."""
    return sorted(hyps.values(), key=lambda h: (-(h.net if h.net is not None else -9), h.id))


def conclusion(hyps: Dict[str, HypothesisResult]) -> dict:
    """Primary cause, contributing causes, weakened/ruled out, or 'insufficient evidence' (never invents a diagnosis)."""
    order = ranked(hyps)
    strong = [h for h in order if h.net is not None and h.net >= PRIMARY_MIN]
    return {"primary": strong[0] if strong else None, "contributing": strong[1:],
            "weak": [h for h in order if h.net is not None and 0.15 <= h.net < PRIMARY_MIN],
            "ruled_out": [h for h in order if h.ruled_out],
            "weakened": [h for h in order if h.net is not None and -0.5 < h.net <= -0.15],
            "unexamined": [h for h in order if h.net is None],
            "inconclusive": not strong}
