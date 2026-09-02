import json
from datetime import datetime
from backend.config import Settings
from backend.exchanges.base import ExchangeConnector
from backend.models import BookLevel, Exchange, Market, OrderBook


def _list(value):
    if isinstance(value, list): return value
    try: return json.loads(value or "[]")
    except (ValueError, TypeError): return []


class PolymarketConnector(ExchangeConnector):
    name = "POLYMARKET"
    def __init__(self, client, settings: Settings):
        super().__init__(client); self.settings = settings

    async def fetch_markets(self, limit: int) -> list[Market]:
        try:
            response = await self.client.get(f"{self.settings.polymarket_gamma_url}/markets",
                params={"active": "true", "closed": "false", "limit": limit})
            response.raise_for_status()
            markets = []
            for raw in response.json():
                outcomes, token_ids = _list(raw.get("outcomes")), _list(raw.get("clobTokenIds"))
                if len(outcomes) != 2 or len(token_ids) != 2: continue
                books = {}
                for outcome, token_id in zip(outcomes, token_ids):
                    try:
                        br = await self.client.get(f"{self.settings.polymarket_clob_url}/book", params={"token_id": token_id})
                        br.raise_for_status(); data = br.json()
                        fr = await self.client.get(f"{self.settings.polymarket_clob_url}/fee-rate/{token_id}")
                        fee = (fr.json().get("base_fee", 0) / 10_000) if fr.is_success else None
                        books[outcome.upper()] = OrderBook(market_id=str(raw.get("conditionId") or raw["id"]), outcome=outcome.upper(),
                            bids=[BookLevel(price=float(x["price"]), quantity=float(x["size"])) for x in data.get("bids", [])],
                            asks=[BookLevel(price=float(x["price"]), quantity=float(x["size"])) for x in data.get("asks", [])],
                            timestamp=datetime.fromisoformat(str(data.get("timestamp", "")).replace("Z", "+00:00")) if data.get("timestamp") else datetime.now().astimezone(),
                            min_order_size=float(data.get("min_order_size", 5)), tick_size=float(data.get("tick_size", .01)),
                            fee_rate=fee, fee_model="polymarket_dynamic")
                    except Exception:
                        continue
                markets.append(Market(exchange=Exchange.POLYMARKET, market_id=str(raw.get("conditionId") or raw["id"]),
                    event_id=str(raw.get("eventId") or ""), title=raw.get("question") or raw.get("title") or "Untitled",
                    description=raw.get("description") or "", resolution_rules=raw.get("description") or "",
                    outcomes=[str(x).upper() for x in outcomes], outcome_ids=dict(zip([str(x).upper() for x in outcomes], token_ids)),
                    close_time=raw.get("endDate"), settlement_source=raw.get("resolutionSource") or "", books=books))
            self.success(); return markets
        except Exception as exc:
            self.failure(exc); raise

