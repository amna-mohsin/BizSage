"""Shared fictional-case fixtures for repeatable expert-system and DSS tests."""
import json
from pathlib import Path

from expert_system.reasoning_controller import ReasoningSession

CASES = json.loads((Path(__file__).resolve().parent.parent / "demo_data" / "cases.json").read_text())


def case_session(key="karachi_family_restaurant") -> ReasoningSession:
    """Build and analyze an isolated session from one bundled demonstration case."""
    c = CASES[key]
    s = ReasoningSession()
    s.set_inputs(dict(c["raw"]), [dict(r) for r in c["history"]], dict(c["profile"]))
    s.analyze()
    return s


def empty_session() -> ReasoningSession:
    """Build an analyzed session with no supplied evidence."""
    s = ReasoningSession()
    s.analyze()
    return s
