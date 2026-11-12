"""Parse owner-entered numbers, uncertainty words, and Urdu-English terms into rule-friendly values.

Parsing distinguishes known, approximate, unknown, and invalid answers so the reasoning engine
can preserve uncertainty instead of treating unclear text as a negative answer.
"""
import re
from typing import Optional, Tuple

from config import APPROX_CERTAINTY

UNKNOWN_WORDS = {"", "?", "unknown", "not sure", "dont know", "don't know", "do not know", "pata nahi", "pata nahin",
                 "maloom nahi", "na maloom", "no idea", "n/a", "na", "none given"}
MULT = {"k": 1e3, "thousand": 1e3, "lac": 1e5, "lacs": 1e5, "lakh": 1e5, "lakhs": 1e5, "m": 1e6, "million": 1e6,
        "crore": 1e7, "cr": 1e7, "%": 1, "percent": 1, "pc": 1}
SYNONYMS = {"kam": "low", "bohat kam": "low", "bahut kam": "low", "thora": "medium", "thoda": "medium", "theek": "medium",
            "normal": "medium", "average": "medium", "moderate": "medium", "zyada": "high", "ziada": "high",
            "bohat zyada": "very high", "bahut zyada": "very high", "bohat ziada": "very high", "nahi": "none", "koi nahi": "none",
            "zero": "none", "ek": "one", "do": "two", "kai": "many", "bohat": "many"}
NUM_RE = re.compile(r"^(?:rs\.?|pkr)?\s*([-+]?\d[\d,]*\.?\d*)\s*(k|thousand|lacs?|lakhs?|m|million|crore|cr|%|percent|pc)?$")

YES = {"yes", "y", "haan", "han", "ha", "ji", "ji haan", "true", "definitely", "sure", "yeah"}
NO = {"no", "n", "nahi", "nahin", "na", "false", "never"}
PROB_YES = {"probably", "maybe", "probably yes", "quite possible", "i think so", "shayad"}
PROB_NO = {"probably not", "probably no", "i think not", "shayad nahi"}


def is_unknown(text: Optional[str]) -> bool:
    return (text or "").strip().lower() in UNKNOWN_WORDS


def parse_number(text: str) -> Tuple[Optional[float], str]:
    """Returns (value, status) where status is 'ok', 'unknown' or 'invalid'."""
    t = (text or "").strip().lower()
    if t in UNKNOWN_WORDS:
        return None, "unknown"
    m = NUM_RE.match(t)
    if not m:
        return None, "invalid"
    try:
        value = float(m.group(1).replace(",", ""))
    except ValueError:
        return None, "invalid"
    return value * MULT.get(m.group(2) or "", 1), "ok"


def parse_numeric_answer(text: str, qualitative: Optional[dict] = None) -> Tuple[Optional[float], float, str]:
    """Accepts a number ('15', '18%', 'Rs 4.5 lac') OR a word ('high', 'zyada').
    Returns (value, certainty, status). Words give an approximate value, so certainty is lower."""
    value, status = parse_number(text)
    if status == "ok":
        return value, 1.0, "ok"
    if status == "unknown":
        return None, 1.0, "unknown"
    word = SYNONYMS.get((text or "").strip().lower(), (text or "").strip().lower())
    if qualitative and word in qualitative:
        return float(qualitative[word]), APPROX_CERTAINTY, "approximate"
    return None, 1.0, "invalid"


def parse_boolean_text(text: str) -> Tuple[Optional[bool], float]:
    """Free-text yes/no. Returns (value, certainty); value None means unknown."""
    t = (text or "").strip().lower()
    if t in YES:
        return True, 1.0
    if t in NO:
        return False, 1.0
    if t in PROB_YES:
        return True, 0.7
    if t in PROB_NO:
        return False, 0.7
    return None, 1.0


# The five answer choices shown for yes/no questions (the "I am not sure / maybe / definitely" vocabulary)
BOOLEAN_CHOICES = [
    ("Yes, definitely", True, 1.0),
    ("Probably yes", True, 0.7),
    ("Not sure / don't know", None, 1.0),
    ("Probably no", False, 0.7),
    ("No, definitely not", False, 1.0),
]
