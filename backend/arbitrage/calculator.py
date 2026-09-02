from __future__ import annotations
from backend.arbitrage.depth import walk_asks, common_depth
from backend.models import Exchange, LegResult, OrderBook


def fee_for(book: OrderBook, quantity: float, notional: float, vwap: float) -> float:
    if book.fee_rate is None:
        return 0.0
    if book.fee_model == "polymarket_dynamic":
        return quantity * book.fee_rate * vwap * (1 - vwap)
    if book.fee_model == "kalshi_profit":
        # Conservative taker estimate; exchange schedules can vary by series.
        return book.fee_rate * quantity * vwap * (1 - vwap)
    return notional * book.fee_rate


def calculate_basket(
    legs: list[tuple[Exchange, OrderBook]], quantity: float | None = None,
    max_capital: float | None = None, payout_per_bundle: float = 1.0,
) -> dict:
    if len(legs) < 2:
        raise ValueError("a basket requires at least two legs")
    capacity_qty = common_depth([book.asks for _, book in legs])
    if capacity_qty <= 0:
        raise ValueError("no common executable depth")
    target = min(quantity or capacity_qty, capacity_qty)

    def compute(qty: float):
        results, cost, fees = [], 0.0, 0.0
        for exchange, book in legs:
            fill = walk_asks(book.asks, qty)
            fee = fee_for(book, qty, fill.notional, fill.vwap)
            cost += fill.notional
            fees += fee
            results.append(LegResult(exchange=exchange, market_id=book.market_id,
                outcome=book.outcome, quantity=qty, vwap=fill.vwap,
                notional=fill.notional, fee=fee, levels_used=fill.levels_used))
        return results, cost, fees

    if max_capital is not None:
        lo, hi = 0.0, target
        for _ in range(50):
            mid = (lo + hi) / 2
            _, c, f = compute(max(mid, 1e-12))
            if c + f <= max_capital:
                lo = mid
            else:
                hi = mid
        target = lo
    if target <= 1e-8:
        raise ValueError("capital limit is below minimum executable size")
    results, raw_cost, fees = compute(target)
    capital = raw_cost + fees
    payout = target * payout_per_bundle
    profit = payout - capital
    return {"legs": results, "quantity": target, "raw_cost": raw_cost,
            "capital_required": capital, "minimum_payout": payout,
            "fees": fees, "net_profit": profit,
            "net_roi": profit / capital if capital else 0.0,
            "capacity": capital}

