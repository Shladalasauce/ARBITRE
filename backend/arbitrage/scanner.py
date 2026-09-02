import hashlib
from datetime import datetime, timezone
from backend.arbitrage.calculator import calculate_basket
from backend.config import Settings
from backend.market_matching.matcher import find_matches
from backend.models import Exchange, Market, MatchConfidence, Opportunity
from backend.risk.engine import assess


def _opportunity(event, strategy, confidence, score, reasons, differences, legs, settings):
    calc = calculate_basket(legs, max_capital=settings.max_capital_per_opportunity)
    key = "|".join(f"{x[0]}:{x[1].market_id}:{x[1].outcome}" for x in legs)
    ident = hashlib.sha256(f"{strategy}|{key}".encode()).hexdigest()[:16]
    books = [x[1] for x in legs]
    top_cost = sum(x.asks[0].price for x in books)
    actual_unit_cost = calc["raw_cost"] / calc["quantity"]
    slippage = max(0, (actual_unit_cost - top_cost) * calc["quantity"])
    op = Opportunity(id=ident,event=event,strategy=strategy,match_confidence=confidence,match_score=score,
        match_reasons=reasons,resolution_differences=differences,slippage=slippage,
        freshness_seconds=0,liquidity_score=min(100,calc["quantity"]),execution_risk="HIGH",classification="REVIEW",**calc)
    return assess(op, books, settings)


def scan(markets_a: list[Market], markets_b: list[Market], settings: Settings) -> tuple[list, list]:
    opportunities, matches = [], find_matches(markets_a, markets_b)
    for match in matches:
        for outcome_a, outcome_b in (("YES","NO"),("NO","YES")):
            if outcome_a in match.market_a.books and outcome_b in match.market_b.books:
                try:
                    opportunities.append(_opportunity(match.market_a.title,"CROSS_MARKET_BINARY",match.confidence,
                        match.score,match.reasons,match.differences,
                        [(match.market_a.exchange,match.market_a.books[outcome_a]),
                         (match.market_b.exchange,match.market_b.books[outcome_b])],settings))
                except ValueError: pass
    for market in markets_a + markets_b:
        if all(x in market.books for x in ("YES","NO")):
            try:
                opportunities.append(_opportunity(market.title,"SAME_MARKET_BINARY",MatchConfidence.VERIFIED,1,
                    ["Complementary outcomes in the same binary contract"],[],
                    [(market.exchange,market.books["YES"]),(market.exchange,market.books["NO"])],settings))
            except ValueError: pass
        elif len(market.outcomes) > 2 and all(x in market.books for x in market.outcomes):
            try:
                opportunities.append(_opportunity(market.title,"MULTI_OUTCOME_BASKET",MatchConfidence.VERIFIED,1,
                    ["Complete mutually-exclusive outcome set from one market"],[],
                    [(market.exchange,market.books[x]) for x in market.outcomes],settings))
            except ValueError: pass
    opportunities = [x for x in opportunities if x.net_profit > 0]
    opportunities.sort(key=lambda x: x.net_profit, reverse=True)
    return opportunities, matches

