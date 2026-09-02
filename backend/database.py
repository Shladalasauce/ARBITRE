import json
import sqlite3
import threading
from pathlib import Path
from backend.models import Opportunity, PaperTrade


class Database:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def connect(self):
        db = sqlite3.connect(self.path, check_same_thread=False)
        db.row_factory = sqlite3.Row
        return db

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS opportunities (
              id TEXT PRIMARY KEY, detected_at TEXT NOT NULL, event TEXT NOT NULL,
              net_profit REAL NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS paper_trades (
              id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, opportunity_id TEXT NOT NULL,
              capital REAL NOT NULL, profit REAL NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS errors (
              id INTEGER PRIMARY KEY, timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
              component TEXT NOT NULL, message TEXT NOT NULL);
            """)

    def save_opportunity(self, item: Opportunity):
        with self._lock, self.connect() as db:
            db.execute("INSERT OR REPLACE INTO opportunities VALUES (?,?,?,?,?)",
                       (item.id, item.detected_at.isoformat(), item.event, item.net_profit, item.model_dump_json()))

    def save_paper_trade(self, trade: PaperTrade):
        with self._lock, self.connect() as db:
            db.execute("INSERT INTO paper_trades VALUES (?,?,?,?,?,?,?)",
                       (trade.id, trade.timestamp.isoformat(), trade.opportunity_id,
                        trade.capital_deployed, trade.theoretical_profit, trade.status, trade.model_dump_json()))

    def paper_trades(self) -> list[dict]:
        with self.connect() as db:
            return [json.loads(x["payload"]) for x in db.execute("SELECT payload FROM paper_trades ORDER BY timestamp DESC")]

    def log_error(self, component: str, message: str):
        with self.connect() as db:
            db.execute("INSERT INTO errors(component,message) VALUES (?,?)", (component, message[:2000]))

