from datetime import datetime
from backend.config import Settings
from backend.exchanges.base import ExchangeConnector
from backend.models import BookLevel, Exchange, Market, OrderBook


class KalshiConnector(ExchangeConnector):
    name = "KALSHI"
    def __init__(self, client, settings: Settings):
        super().__init__(client); self.settings = settings

    async def fetch_markets(self, limit: int) -> list[Market]:
        try:
            r = await self.client.get(f"{self.settings.kalshi_api_url}/markets", params={"status":"open", "limit":limit})
            r.raise_for_status(); result = []
            for raw in r.json().get("markets", []):
                ticker = raw["ticker"]
                try:
                    br = await self.client.get(f"{self.settings.kalshi_api_url}/markets/{ticker}/orderbook")
                    br.raise_for_status(); data = br.json().get("orderbook_fp", {})
                    yes_bids = [BookLevel(price=float(p), quantity=float(q)) for p,q in data.get("yes_dollars", [])]
                    no_bids = [BookLevel(price=float(p), quantity=float(q)) for p,q in data.get("no_dollars", [])]
                    # A NO bid at p is an executable YES ask at 1-p, and vice versa.
                    yes_asks = [BookLevel(price=round(1-x.price, 4), quantity=x.quantity) for x in no_bids]
                    no_asks = [BookLevel(price=round(1-x.price, 4), quantity=x.quantity) for x in yes_bids]
                    now = datetime.now().astimezone()
                    # Fee coefficients vary by series; unknown intentionally blocks verified execution.
                    books = {"YES": OrderBook(market_id=ticker,outcome="YES",bids=yes_bids,asks=yes_asks,timestamp=now,fee_rate=None,fee_model="kalshi_profit"),
                             "NO": OrderBook(market_id=ticker,outcome="NO",bids=no_bids,asks=no_asks,timestamp=now,fee_rate=None,fee_model="kalshi_profit")}
                except Exception:
                    books = {}
                rules = " ".join(filter(None, [raw.get("rules_primary"), raw.get("rules_secondary")]))
                result.append(Market(exchange=Exchange.KALSHI, market_id=ticker, event_id=raw.get("event_ticker", ""),
                    title=raw.get("title") or raw.get("subtitle") or ticker, description=raw.get("subtitle") or "",
                    resolution_rules=rules, close_time=raw.get("close_time"), settlement_source=raw.get("settlement_source_url") or "", books=books))
            self.success(); return result
        except Exception as exc:
            self.failure(exc); raise

