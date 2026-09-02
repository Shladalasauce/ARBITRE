from abc import ABC, abstractmethod
from datetime import datetime, timezone
import httpx
from backend.models import Market


class ExchangeConnector(ABC):
    name: str
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.connected = False
        self.last_update: datetime | None = None
        self.error: str | None = None

    @abstractmethod
    async def fetch_markets(self, limit: int) -> list[Market]: ...

    def success(self):
        self.connected, self.error = True, None
        self.last_update = datetime.now(timezone.utc)

    def failure(self, exc: Exception):
        self.connected, self.error = False, str(exc)

    def status(self):
        return {"connected": self.connected, "last_update": self.last_update,
                "error": self.error, "mode": "PUBLIC READ-ONLY"}

