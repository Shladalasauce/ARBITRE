from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_path: Path = Path("arbitrage_terminal.db")
    paper_balance: float = 10_000.0
    demo_mode: bool = True
    poll_interval_seconds: int = 30
    market_limit_per_exchange: int = 40
    min_net_roi: float = 0.005
    min_expected_profit: float = 1.0
    max_capital_per_opportunity: float = 1_000.0
    max_total_exposure: float = 5_000.0
    max_book_age_seconds: int = 60
    min_liquidity: float = 5.0
    min_match_confidence: str = "VERIFIED"
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"
    kalshi_api_url: str = "https://external-api.kalshi.com/trade-api/v2"
    kalshi_api_key_id: str = ""
    kalshi_private_key_path: str = ""
    live_trading_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

