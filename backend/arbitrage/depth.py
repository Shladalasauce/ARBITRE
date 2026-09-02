from dataclasses import dataclass
from backend.models import BookLevel


@dataclass
class DepthFill:
    quantity: float
    notional: float
    vwap: float
    levels_used: int


def walk_asks(levels: list[BookLevel], quantity: float) -> DepthFill:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    remaining, notional, used = quantity, 0.0, 0
    for level in sorted(levels, key=lambda x: x.price):
        take = min(remaining, level.quantity)
        if take > 0:
            notional += take * level.price
            remaining -= take
            used += 1
        if remaining <= 1e-12:
            break
    filled = quantity - remaining
    if remaining > 1e-9:
        raise ValueError(f"insufficient depth: requested {quantity}, available {filled}")
    return DepthFill(filled, notional, notional / filled, used)


def common_depth(books: list[list[BookLevel]]) -> float:
    return min((sum(x.quantity for x in levels) for levels in books), default=0.0)

