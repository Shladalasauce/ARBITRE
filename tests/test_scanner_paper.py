from backend.arbitrage.scanner import scan
from backend.config import Settings
from backend.execution.paper import simulate
from backend.exchanges.demo import demo_markets


def test_demo_cross_market_profit_is_depth_aware():
    a,b=demo_markets(); opportunities,matches=scan(a,b,Settings(max_capital_per_opportunity=1000,min_expected_profit=0))
    cross=[x for x in opportunities if x.strategy=="CROSS_MARKET_BINARY"]
    assert matches[0].confidence == "VERIFIED"
    assert cross
    assert cross[0].net_profit > 0
    assert cross[0].quantity <= 350


def test_paper_balance_failure_and_fill():
    a,b=demo_markets(); opportunities,_=scan(a,b,Settings(min_expected_profit=0))
    op=opportunities[0]
    assert simulate(op,0).status == "FAILED_BALANCE"
    assert simulate(op,10_000).status == "SIMULATED_FILLED"

