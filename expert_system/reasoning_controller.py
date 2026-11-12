"""Iterative Reasoning Controller.

One investigation = repeat { infer -> update hypotheses -> pick the most useful question -> take the answer }
until a safe termination condition is met (no useful question left, question limit reached, or the owner finishes).
"""
from copy import deepcopy
from typing import Dict, List, Optional

from calculations import metrics
from config import MAX_QUESTIONS
from expert_system import data_quality, hypothesis_manager, inference_engine, question_selector
from expert_system.explanation import conclusion_text, missing_evidence, why_question
from expert_system.knowledge_loader import KnowledgeBase, load_kb
from expert_system.working_memory import WorkingMemory

BLANK_MONTHS = 6


def blank_history(n: int = BLANK_MONTHS) -> List[dict]:
    return [{"revenue": None, "expenses": None, "customers": None, "food_cost": None} for _ in range(n)]


class ReasoningSession:
    def __init__(self, kb: Optional[KnowledgeBase] = None):
        self.kb = kb or load_kb()
        self.profile: dict = {}
        self.raw: dict = {}
        self.raw_certainty: dict = {}
        self.history: List[dict] = blank_history()
        self.answers: Dict[str, dict] = {}
        self.dont_know: set = set()
        self.confirmed: set = set()
        self.asked: List[str] = []
        self.steps: List[dict] = []
        self.finished = False
        self.state: Optional[dict] = None

    # ------------------------------------------------------------------ inputs
    def set_inputs(self, raw: dict = None, history: List[dict] = None, profile: dict = None) -> None:
        if raw is not None:
            self.raw = {k: v for k, v in raw.items() if v is not None}
            self.raw_certainty = {k: self.raw_certainty.get(k, 1.0) for k in self.raw}
        if history is not None:
            self.history = history
        if profile is not None:
            self.profile = profile

    def has_data(self) -> bool:
        return any(r.get("revenue") for r in self.history)

    # ------------------------------------------------------------------ analysis
    def analyze(self) -> dict:
        kb = self.kb
        clean_raw, clean_hist, issues = data_quality.validate_inputs(kb, self.raw, self.history)
        derived = metrics.derive(clean_raw, clean_hist, self.profile)
        wm = WorkingMemory()
        for k, v in derived.items():
            wm.set(k, v, 1.0, "derived")
        for fid in kb.facts:
            if kb.facts[fid]["source"] == "input" and fid in clean_raw:
                wm.set(fid, clean_raw[fid], self.raw_certainty.get(fid, 1.0), "input")
        redundant_answers = []
        for fid, a in self.answers.items():
            if wm.has(fid):                       # a measured value already exists: keep it, record the duplicate
                redundant_answers.append(fid)
            elif a["value"] is not None:
                wm.set(fid, a["value"], a["certainty"], "answer")
        for fid in self.dont_know:
            if not wm.has(fid):
                wm.mark_dont_know(fid)
        conflicts = data_quality.check_consistency(kb, wm)
        for c in conflicts:
            if c["severity"] == "conflict":
                wm.disputed.update(c["disputes"])
        wm.confirmed = set(self.confirmed)
        res = inference_engine.run(kb, wm)
        hyps = hypothesis_manager.evaluate(kb, res)
        concl = hypothesis_manager.conclusion(hyps)
        followups = {f.next_question for f in res.firings if f.next_question}
        ranked_q = question_selector.rank_questions(kb, res.memory, res, hyps, set(self.asked) | self.dont_know, followups)
        clarify = [fid for fid in sorted(wm.disputed) if fid not in self.confirmed and fid in self.answers]
        self.state = {
            "derived": derived, "facts": res.memory.values(), "wm": res.memory, "issues": issues, "conflicts": conflicts,
            "redundant_answers": redundant_answers, "result": res, "hypotheses": hyps, "conclusion": concl,
            "ranked_questions": ranked_q, "clarify": clarify, "missing": missing_evidence(kb, res),
            "completeness": data_quality.missing_summary(kb, clean_raw, clean_hist),
            "clean_raw": clean_raw, "clean_history": clean_hist,
        }
        return self.state

    def nets(self) -> Dict[str, Optional[float]]:
        return {h: x.net for h, x in self.state["hypotheses"].items()} if self.state else {}

    # ------------------------------------------------------------------ questioning loop
    def termination(self) -> Optional[str]:
        if self.finished:
            return "The owner finished the investigation."
        if len(self.asked) >= MAX_QUESTIONS:
            return f"Question limit reached ({MAX_QUESTIONS})."
        if self.state and not self.state["ranked_questions"] and not self.state["clarify"]:
            return "No remaining question can change the conclusion."
        return None

    def current_question(self) -> Optional[dict]:
        if not self.state or self.termination():
            return None
        if self.state["clarify"]:
            fid = self.state["clarify"][0]
            msgs = [c["message"] for c in self.state["conflicts"] if fid in c["disputes"]]
            return {"type": "clarify", "fact": fid, "reason": "Two pieces of information conflict. " + " ".join(msgs)
                    + " The rules that use this answer are paused until you confirm or correct it.", "hypotheses": [], "rules": [], "score": 99}
        q = dict(self.state["ranked_questions"][0])
        q["type"] = "question"
        q["why"] = why_question(self.kb, q, self.state["hypotheses"])
        return q

    def _snapshot_change(self, before: Dict[str, Optional[float]]) -> List[dict]:
        out = []
        for hid, h in self.state["hypotheses"].items():
            b, a = before.get(hid), h.net
            if b is None and a is None:
                continue
            if b is None or a is None or abs(a - b) >= 0.01:
                out.append({"hypothesis": h.name, "before": b, "after": a, "label": h.label,
                            "direction": "new" if b is None else ("up" if a > b else "down")})
        return out

    def _record(self, fid: str, answer_text: str, before: dict) -> None:
        self.analyze()
        self.steps.append({"n": len(self.steps) + 1, "fact": fid, "question": self.kb.facts[fid].get("question", fid),
                           "answer": answer_text, "changes": self._snapshot_change(before)})

    def answer(self, fid: str, value, certainty: float = 1.0, text: str = "") -> None:
        """Records an answer. value None means 'don't know' (stored as UNKNOWN, never as No)."""
        before = self.nets()
        spec = self.kb.facts[fid]
        if fid not in self.asked:
            self.asked.append(fid)
        self.confirmed.discard(fid)
        if value is None:
            self.dont_know.add(fid)
            self.answers.pop(fid, None)
            self.raw.pop(fid, None)
        else:
            self.dont_know.discard(fid)
            if spec["type"] == "number":
                self.raw[fid] = float(value)
                self.raw_certainty[fid] = certainty
            else:
                self.answers[fid] = {"value": value, "certainty": certainty, "text": text}
        self._record(fid, text or ("Don't know" if value is None else str(value)), before)

    def confirm(self, fid: str) -> None:
        """Owner insists on a disputed answer: the rules using it are resumed (with the conflict still reported)."""
        before = self.nets()
        self.confirmed.add(fid)
        self._record(fid, "Confirmed my answer despite the conflict", before)

    def finish(self) -> None:
        self.finished = True
        if self.state is None:
            self.analyze()

    def reset_investigation(self) -> None:
        self.answers, self.dont_know, self.confirmed, self.asked, self.steps, self.finished = {}, set(), set(), [], [], False
        for fid in ("discount_pct", "wastage_pct", "overdue_installments", "labour_hours_month"):
            pass   # numeric answers live in raw; the owner can edit them on the assessment page
        self.analyze()

    # ------------------------------------------------------------------ outputs
    def summary_text(self) -> str:
        return conclusion_text(self.state["conclusion"]) if self.state else "No analysis yet."

    def export_state(self) -> dict:
        return {"profile": self.profile, "raw": self.raw, "raw_certainty": self.raw_certainty, "history": self.history,
                "answers": self.answers, "dont_know": sorted(self.dont_know), "confirmed": sorted(self.confirmed),
                "asked": self.asked, "steps": self.steps, "finished": self.finished}

    def load_state(self, d: dict) -> None:
        self.profile, self.raw = d.get("profile", {}), d.get("raw", {})
        self.raw_certainty = d.get("raw_certainty", {})
        self.history = d.get("history") or blank_history()
        self.answers, self.dont_know = d.get("answers", {}), set(d.get("dont_know", []))
        self.confirmed, self.asked = set(d.get("confirmed", [])), d.get("asked", [])
        self.steps, self.finished = d.get("steps", []), d.get("finished", False)
        self.analyze()

    def clone_with(self, raw_overrides: dict = None, history_overrides: List[dict] = None) -> "ReasoningSession":
        """A copy for what-if simulation (answers kept, inputs changed). Does not touch the original."""
        s = ReasoningSession(self.kb)
        s.load_state(deepcopy(self.export_state()))
        if raw_overrides:
            s.raw.update(raw_overrides)
        if history_overrides is not None:
            s.history = history_overrides
        s.analyze()
        return s
