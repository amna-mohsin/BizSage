"""Certainty-factor arithmetic (MYCIN style). Scores are EVIDENCE-BASED CONFIDENCE, not statistical probabilities."""
from typing import Iterable, Tuple

from config import BANDS


def combine(values: Iterable[float]) -> float:
    """Combines positive certainty factors: cf = cf1 + cf2 * (1 - cf1). Always stays below 1."""
    p = 0.0
    for v in values:
        # Each new item adds only the portion not already explained by accumulated support.
        p = p + v * (1 - p)
    return p


def net_certainty(pos: float, neg: float) -> float:
    """Merges support and contradiction into one score in [-1, 1]."""
    low = min(pos, neg)
    return (pos - neg) / (1 - low) if low < 1 else 0.0


def label_for(net: float) -> Tuple[str, str]:
    """Map a certainty-factor score to the plain-language band shown to the owner."""
    for limit, text, tone in BANDS:
        if net >= limit:
            return text, tone
    return BANDS[-1][1], BANDS[-1][2]
