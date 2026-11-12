"""Explanation facility: why was this question asked, why this conclusion, what is still missing."""
from typing import Dict, List

from expert_system.hypothesis_manager import HypothesisResult
from expert_system.inference_engine import InferenceResult
from expert_system.knowledge_loader import KnowledgeBase
from expert_system.rule_interpreter import UNKNOWN

DISCLAIMER = ("BizSage is a decision-support and educational expert system. Its findings are evidence-based confidence scores built from "
              "rules and the information you entered. They are not statistical probabilities and not professional financial advice. "
              "Please confirm important decisions with a qualified accountant or business adviser.")


def why_question(kb: KnowledgeBase, q: dict, hyps: Dict[str, HypothesisResult]) -> str:
    """Explain which unresolved causes and rules make the selected question useful."""
    lines = [q["reason"]]
    cur = [f"{hyps[h].name} (now: {hyps[h].label})" for h in q["hypotheses"][:4]]
    if cur:
        lines.append("Currently being investigated: " + "; ".join(cur) + ".")
    lines.append("Rules waiting for this answer: " + ", ".join(q["rules"][:6]) + ".")
    return " ".join(lines)


def missing_evidence(kb: KnowledgeBase, res: InferenceResult) -> Dict[str, List[str]]:
    """For each hypothesis: which facts, if known, could still change its support."""
    out: Dict[str, set] = {}
    # Only UNKNOWN rules can still change a finding; false rules are already resolved.
    for rule in kb.rules:
        if res.rule_status.get(rule["id"]) != UNKNOWN:
            continue
        for fid in res.unknown_facts.get(rule["id"], []):
            for e in rule["effects"]:
                out.setdefault(e["hypothesis"], set()).add(kb.facts[fid]["label"])
    return {h: sorted(v) for h, v in out.items()}


def hypothesis_lines(h: HypothesisResult) -> dict:
    """Prepare readable evidence-for/against text, preserving redundancy annotations."""
    return {
        "for": [f"[{e.rule_id}] {e.explanation}" + (" (overlapping evidence, counted partly)" if e.consolidated else "") for e in h.evidence_for],
        "against": [f"[{e.rule_id}] {e.explanation}" for e in h.evidence_against],
        "notes": h.redundant,
    }


def conclusion_text(c: dict) -> str:
    if c["inconclusive"]:
        return "Insufficient evidence to determine the primary cause. More information is needed; the system will not guess."
    p = c["primary"]
    text = f"Most supported finding: {p.name} ({p.label}, support score {p.percent}/100)."
    if c["contributing"]:
        text += " Other contributing causes: " + ", ".join(h.name for h in c["contributing"]) + "."
    if c["ruled_out"]:
        text += " Ruled out by the evidence: " + ", ".join(h.name for h in c["ruled_out"]) + "."
    return text
