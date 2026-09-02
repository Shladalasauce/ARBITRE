from __future__ import annotations
import hashlib
import re
import unicodedata
from difflib import SequenceMatcher
from backend.market_matching.resolution_checker import rule_differences
from backend.models import Market, MarketMatch, MatchConfidence


STOP = {"will", "the", "a", "an", "be", "is", "to", "of", "in", "on", "by", "market"}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join(x for x in re.findall(r"[a-z0-9]+", value) if x not in STOP)


def match_markets(a: Market, b: Market) -> MarketMatch:
    na, nb = normalize(a.title), normalize(b.title)
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / max(1, len(ta | tb))
    sequence = SequenceMatcher(None, na, nb).ratio()
    score = 0.65 * jaccard + 0.35 * sequence
    reasons = [f"Normalized title token overlap: {jaccard:.0%}", f"Title sequence similarity: {sequence:.0%}"]
    if a.event_id and a.event_id == b.event_id:
        score = max(score, 0.98)
        reasons.append("Exchange event identifiers are identical")
    differences = rule_differences(a.resolution_rules, b.resolution_rules, a.close_time, b.close_time,
                                   a.settlement_source, b.settlement_source)
    if differences:
        score = max(0, score - min(0.35, 0.08 * len(differences)))
    if score >= .92 and not differences and a.resolution_rules and b.resolution_rules:
        confidence = MatchConfidence.VERIFIED
    elif score >= .72 and len(differences) <= 1:
        confidence = MatchConfidence.LIKELY
    elif score >= .48:
        confidence = MatchConfidence.AMBIGUOUS
    else:
        confidence = MatchConfidence.REJECTED
    ident = hashlib.sha256(f"{a.exchange}:{a.market_id}|{b.exchange}:{b.market_id}".encode()).hexdigest()[:16]
    return MarketMatch(id=ident, market_a=a, market_b=b, confidence=confidence,
                       score=score, reasons=reasons, differences=differences)


def find_matches(left: list[Market], right: list[Market], minimum_score: float = .48) -> list[MarketMatch]:
    candidates = []
    for a in left:
        best = max((match_markets(a, b) for b in right), key=lambda x: x.score, default=None)
        if best and best.score >= minimum_score:
            candidates.append(best)
    return candidates

