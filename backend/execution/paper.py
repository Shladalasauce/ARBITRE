from uuid import uuid4
from backend.models import Opportunity, PaperTrade


def simulate(opportunity: Opportunity, available_balance: float) -> PaperTrade:
    if opportunity.capital_required > available_balance:
        return PaperTrade(id=str(uuid4()),opportunity_id=opportunity.id,capital_deployed=0,quantity=0,
            theoretical_profit=0,roi=0,status="FAILED_BALANCE",details={"reason":"Insufficient virtual balance"})
    if opportunity.freshness_seconds > 60:
        return PaperTrade(id=str(uuid4()),opportunity_id=opportunity.id,capital_deployed=0,quantity=0,
            theoretical_profit=0,roi=0,status="FAILED_STALE",details={"reason":"Snapshot became stale"})
    return PaperTrade(id=str(uuid4()),opportunity_id=opportunity.id,
        capital_deployed=opportunity.capital_required,quantity=opportunity.quantity,
        theoretical_profit=opportunity.net_profit,roi=opportunity.net_roi,status="SIMULATED_FILLED",
        details={"legs":[x.model_dump(mode="json") for x in opportunity.legs],
                 "fees":opportunity.fees,"slippage":opportunity.slippage,
                 "subsequent_market_movement":None,
                 "note":"Depth snapshot was re-used; no orders were sent."})

