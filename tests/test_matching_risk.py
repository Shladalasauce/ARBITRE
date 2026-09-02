from datetime import datetime, timedelta, timezone
from backend.config import Settings
from backend.market_matching.matcher import match_markets
from backend.models import BookLevel, Exchange, Market, MatchConfidence, Opportunity, OrderBook
from backend.risk.engine import assess


RULE="Resolves Yes if Alice receives at least 50 votes by January 1 2027 according to the official result."
def market(exchange,title=RULE,rules=RULE,close=None):
    return Market(exchange=exchange,market_id=str(exchange),title=title,resolution_rules=rules,
                  close_time=close or datetime(2027,1,2,tzinfo=timezone.utc),settlement_source="Official result")


def test_identical_rules_verified():
    result=match_markets(market(Exchange.POLYMARKET),market(Exchange.KALSHI))
    assert result.confidence == MatchConfidence.VERIFIED
    assert result.differences == []


def test_threshold_and_cutoff_difference_not_verified():
    b=market(Exchange.KALSHI,rules="Resolves yes if Alice receives more than 51 votes.",
             close=datetime(2027,1,3,tzinfo=timezone.utc))
    result=match_markets(market(Exchange.POLYMARKET),b)
    assert result.confidence != MatchConfidence.VERIFIED
    assert any("Cutoff" in x for x in result.differences)
    assert any("numeric" in x for x in result.differences)


def test_stale_and_unknown_fee_rejected():
    old=datetime.now(timezone.utc)-timedelta(minutes=5)
    b=OrderBook(market_id="m",outcome="YES",asks=[BookLevel(price=.4,quantity=10)],timestamp=old,fee_rate=None)
    op=Opportunity(id="x",event="x",strategy="test",match_confidence=MatchConfidence.VERIFIED,match_score=1,
        legs=[],quantity=10,capital_required=8,minimum_payout=10,fees=0,slippage=0,net_profit=2,net_roi=.25,
        capacity=8,freshness_seconds=0,liquidity_score=10,execution_risk="LOW",classification="VERIFIED")
    result=assess(op,[b],Settings())
    assert not result.executable
    assert "market data is stale" in result.rejection_reasons
    assert "fee schedule could not be verified" in result.rejection_reasons

