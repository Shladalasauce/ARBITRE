import pytest
from backend.arbitrage.calculator import calculate_basket, fee_for
from backend.arbitrage.depth import walk_asks
from backend.models import BookLevel, Exchange, OrderBook


def book(outcome, levels, fee=.01, model="flat_notional", minimum=1):
    return OrderBook(market_id="m", outcome=outcome, asks=[BookLevel(price=p,quantity=q) for p,q in levels],
                     fee_rate=fee,fee_model=model,min_order_size=minimum)


def test_walk_depth_and_vwap():
    fill=walk_asks([BookLevel(price=.4,quantity=10),BookLevel(price=.5,quantity=10)],15)
    assert fill.notional == pytest.approx(6.5)
    assert fill.vwap == pytest.approx(6.5/15)
    assert fill.levels_used == 2


def test_partial_liquidity_rejected():
    with pytest.raises(ValueError,match="insufficient depth"):
        walk_asks([BookLevel(price=.4,quantity=2)],3)


def test_basket_depth_fees_and_profit():
    result=calculate_basket([(Exchange.POLYMARKET,book("YES",[(.4,10),(.45,10)])),
                             (Exchange.KALSHI,book("NO",[(.5,15)]))],quantity=15)
    assert result["quantity"] == 15
    assert result["raw_cost"] == pytest.approx(13.75)
    assert result["fees"] == pytest.approx(.1375)
    assert result["net_profit"] == pytest.approx(1.1125)
    assert result["net_roi"] == pytest.approx(1.1125/13.8875)


def test_common_capacity_and_capital_limit():
    result=calculate_basket([(Exchange.POLYMARKET,book("YES",[(.4,100)],0)),
                             (Exchange.KALSHI,book("NO",[(.5,50)],0))],max_capital=18)
    assert result["quantity"] == pytest.approx(20)
    assert result["capital_required"] == pytest.approx(18)


def test_dynamic_fee():
    b=book("YES",[(.5,10)],.03,"polymarket_dynamic")
    assert fee_for(b,10,5,.5)==pytest.approx(.075)
