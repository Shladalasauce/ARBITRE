from datetime import datetime, timezone
from backend.config import Settings
from backend.models import MatchConfidence, Opportunity, OrderBook


RANK = {MatchConfidence.REJECTED: 0, MatchConfidence.AMBIGUOUS: 1,
        MatchConfidence.LIKELY: 2, MatchConfidence.VERIFIED: 3}


def assess(opportunity: Opportunity, books: list[OrderBook], settings: Settings) -> Opportunity:
    reasons = list(opportunity.rejection_reasons)
    age = max((datetime.now(timezone.utc) - b.timestamp).total_seconds() for b in books)
    opportunity.freshness_seconds = max(0, age)
    if age > settings.max_book_age_seconds:
        reasons.append("market data is stale")
    if opportunity.net_roi < settings.min_net_roi:
        reasons.append("net ROI below configured minimum")
    if opportunity.net_profit < settings.min_expected_profit:
        reasons.append("expected profit below configured minimum")
    if opportunity.capital_required > settings.max_capital_per_opportunity + .01:
        reasons.append("capital exceeds per-opportunity limit")
    if opportunity.quantity < settings.min_liquidity:
        reasons.append("liquidity below configured minimum")
    required = MatchConfidence(settings.min_match_confidence)
    if RANK[opportunity.match_confidence] < RANK[required]:
        reasons.append("resolution match confidence below configured minimum")
    if any(b.fee_rate is None for b in books):
        reasons.append("fee schedule could not be verified")
    if any(opportunity.quantity < b.min_order_size for b in books):
        reasons.append("quantity below an exchange minimum order size")
    opportunity.rejection_reasons = sorted(set(reasons))
    opportunity.executable = not reasons
    opportunity.execution_risk = "LOW" if not reasons else ("MEDIUM" if len(reasons) == 1 else "HIGH")
    opportunity.classification = "VERIFIED" if opportunity.executable else ("STALE" if "market data is stale" in reasons else "REVIEW")
    return opportunity

