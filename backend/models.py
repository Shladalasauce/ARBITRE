from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Exchange(StrEnum):
    POLYMARKET = "POLYMARKET"
    KALSHI = "KALSHI"
    DEMO = "DEMO"


class MatchConfidence(StrEnum):
    VERIFIED = "VERIFIED"
    LIKELY = "LIKELY"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"


class BookLevel(BaseModel):
    price: float = Field(ge=0, le=1)
    quantity: float = Field(gt=0)


class OrderBook(BaseModel):
    market_id: str
    outcome: str
    bids: list[BookLevel] = []
    asks: list[BookLevel] = []
    timestamp: datetime = Field(default_factory=utcnow)
    min_order_size: float = 1.0
    tick_size: float = 0.01
    fee_rate: float | None = None
    fee_model: str = "flat_notional"

    @field_validator("bids")
    @classmethod
    def sort_bids(cls, value):
        return sorted(value, key=lambda x: x.price, reverse=True)

    @field_validator("asks")
    @classmethod
    def sort_asks(cls, value):
        return sorted(value, key=lambda x: x.price)


class Market(BaseModel):
    exchange: Exchange
    market_id: str
    event_id: str = ""
    title: str
    description: str = ""
    resolution_rules: str = ""
    outcomes: list[str] = ["YES", "NO"]
    outcome_ids: dict[str, str] = {}
    close_time: datetime | None = None
    settlement_source: str = ""
    status: str = "open"
    timestamp: datetime = Field(default_factory=utcnow)
    books: dict[str, OrderBook] = {}


class MarketMatch(BaseModel):
    id: str
    market_a: Market
    market_b: Market
    confidence: MatchConfidence
    score: float
    reasons: list[str]
    differences: list[str]


class LegResult(BaseModel):
    exchange: Exchange
    market_id: str
    outcome: str
    quantity: float
    vwap: float
    notional: float
    fee: float
    levels_used: int


class Opportunity(BaseModel):
    id: str
    event: str
    strategy: str
    match_confidence: MatchConfidence
    match_score: float
    match_reasons: list[str] = []
    resolution_differences: list[str] = []
    legs: list[LegResult]
    quantity: float
    capital_required: float
    minimum_payout: float
    fees: float
    slippage: float
    net_profit: float
    net_roi: float
    capacity: float
    freshness_seconds: float
    liquidity_score: float
    execution_risk: str
    classification: str
    detected_at: datetime = Field(default_factory=utcnow)
    executable: bool = False
    rejection_reasons: list[str] = []


class PaperTrade(BaseModel):
    id: str
    opportunity_id: str
    timestamp: datetime = Field(default_factory=utcnow)
    capital_deployed: float
    quantity: float
    theoretical_profit: float
    roi: float
    status: str
    details: dict = {}

