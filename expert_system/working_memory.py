"""Working Memory: the facts the system currently believes, with how certain each one is."""
from dataclasses import dataclass
from typing import Dict, Optional, Set


@dataclass
class Fact:
    id: str
    value: object
    certainty: float = 1.0      # 1.0 exact; <1 when the owner answered with a word or "probably"
    source: str = "input"       # input | derived | answer | asserted:<rule id>


class WorkingMemory:
    """Three-valued: a fact is KNOWN (has a value), UNKNOWN (never provided) or explicitly 'don't know'.
    A missing or 'don't know' fact is never treated as False or zero."""

    def __init__(self):
        self.facts: Dict[str, Fact] = {}
        self.dont_know: Set[str] = set()
        self.disputed: Set[str] = set()
        self.confirmed: Set[str] = set()

    def set(self, fid: str, value, certainty: float = 1.0, source: str = "input") -> None:
        """Store a known fact and clear its explicit 'don't know' marker."""
        if value is None:
            return
        self.facts[fid] = Fact(fid, value, certainty, source)
        self.dont_know.discard(fid)

    def mark_dont_know(self, fid: str) -> None:
        """Record explicit uncertainty without converting it into False or zero."""
        self.facts.pop(fid, None)
        self.dont_know.add(fid)

    def get(self, fid: str) -> Optional[Fact]:
        return self.facts.get(fid)

    def has(self, fid: str) -> bool:
        return fid in self.facts

    def is_disputed(self, fid: str) -> bool:
        return fid in self.disputed and fid not in self.confirmed

    def values(self) -> dict:
        return {k: f.value for k, f in self.facts.items()}

    def copy(self) -> "WorkingMemory":
        """Copy facts and resolution metadata so inference can safely add derived assertions."""
        w = WorkingMemory()
        w.facts = {k: Fact(f.id, f.value, f.certainty, f.source) for k, f in self.facts.items()}
        w.dont_know, w.disputed, w.confirmed = set(self.dont_know), set(self.disputed), set(self.confirmed)
        return w
