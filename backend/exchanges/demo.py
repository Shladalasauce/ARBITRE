from datetime import datetime, timezone
from backend.models import BookLevel, Exchange, Market, OrderBook


def demo_markets():
    now = datetime.now(timezone.utc)
    rules = "Resolves Yes if the official national weather service records at least 90 degrees in Central Park on August 15, 2026."
    def book(mid, outcome, asks):
        return OrderBook(market_id=mid, outcome=outcome, asks=[BookLevel(price=p,quantity=q) for p,q in asks],
                         bids=[BookLevel(price=max(.01,p-.02),quantity=q) for p,q in asks], timestamp=now,
                         min_order_size=1, fee_rate=.002, fee_model="flat_notional")
    a = Market(exchange=Exchange.POLYMARKET,market_id="demo-poly-weather",event_id="demo-weather",title="Will Central Park reach at least 90 degrees on August 15, 2026?",
        description=rules,resolution_rules=rules,settlement_source="National Weather Service",close_time="2026-08-16T04:00:00Z",
        books={"YES":book("demo-poly-weather","YES",[(.45,100),(.46,250)]),"NO":book("demo-poly-weather","NO",[(.57,100),(.58,250)])})
    b = Market(exchange=Exchange.KALSHI,market_id="demo-kalshi-weather",event_id="demo-weather",title="Will Central Park reach at least 90 degrees on August 15, 2026?",
        description=rules,resolution_rules=rules,settlement_source="National Weather Service",close_time="2026-08-16T04:00:00Z",
        books={"YES":book("demo-kalshi-weather","YES",[(.48,120),(.49,200)]),"NO":book("demo-kalshi-weather","NO",[(.50,80),(.51,250)])})
    return [a], [b]

