from __future__ import annotations
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.arbitrage.scanner import scan
from backend.config import get_settings
from backend.database import Database
from backend.exchanges.demo import demo_markets
from backend.exchanges.kalshi import KalshiConnector
from backend.exchanges.polymarket import PolymarketConnector
from backend.execution.paper import simulate

logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("arbitrage-terminal")
settings = get_settings(); db = Database(settings.database_path)


class Runtime:
    opportunities = []
    matches = []
    markets = []
    task = None
    mode = "DEMO" if settings.demo_mode else "LIVE READ-ONLY"
runtime = Runtime()


async def refresh(app: FastAPI):
    poly, kalshi = app.state.poly, app.state.kalshi
    try:
        if settings.demo_mode:
            left,right = demo_markets(); poly.success(); kalshi.success()
        else:
            results = await asyncio.gather(poly.fetch_markets(settings.market_limit_per_exchange),
                                           kalshi.fetch_markets(settings.market_limit_per_exchange),return_exceptions=True)
            left = [] if isinstance(results[0],Exception) else results[0]
            right = [] if isinstance(results[1],Exception) else results[1]
            for name,result in zip(("polymarket","kalshi"),results):
                if isinstance(result,Exception): db.log_error(name,str(result)); log.warning("%s refresh failed: %s",name,result)
        runtime.markets = left + right
        runtime.opportunities,runtime.matches = scan(left,right,settings)
        for item in runtime.opportunities: db.save_opportunity(item)
        log.info("refresh complete mode=%s markets=%d matches=%d opportunities=%d",runtime.mode,len(runtime.markets),len(runtime.matches),len(runtime.opportunities))
    except Exception as exc:
        db.log_error("scanner",str(exc)); log.exception("scanner refresh failed")


async def refresh_loop(app):
    while True:
        await refresh(app)
        await asyncio.sleep(max(5,settings.poll_interval_seconds))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.initialize(); app.state.client = httpx.AsyncClient(timeout=12,headers={"User-Agent":"ArbitrageTerminal/1.0"})
    app.state.poly = PolymarketConnector(app.state.client,settings); app.state.kalshi = KalshiConnector(app.state.client,settings)
    await refresh(app); runtime.task = asyncio.create_task(refresh_loop(app))
    yield
    runtime.task.cancel(); await app.state.client.aclose()


app = FastAPI(title="Arbitrage Terminal",version="1.0.0",lifespan=lifespan)
frontend = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static",StaticFiles(directory=frontend),name="static")

@app.get("/")
async def home(): return FileResponse(frontend / "index.html")

@app.get("/api/health")
async def health():
    return {"status":"ok","mode":runtime.mode,"paper_mode":True,"live_trading":False,
            "exchanges":{"POLYMARKET":app.state.poly.status(),"KALSHI":app.state.kalshi.status()}}

@app.get("/api/dashboard")
async def dashboard():
    trades = db.paper_trades(); capital=sum(x["capital_deployed"] for x in trades)
    return {"mode":runtime.mode,"markets_monitored":len(runtime.markets),"matched_markets":len(runtime.matches),
            "live_opportunities":len(runtime.opportunities),"capital_deployable":settings.paper_balance-capital,
            "potential_net_profit":sum(x.net_profit for x in runtime.opportunities),
            "opportunities":[x.model_dump(mode="json") for x in runtime.opportunities]}

@app.post("/api/refresh")
async def force_refresh(): await refresh(app); return {"ok":True}

@app.post("/api/paper/{opportunity_id}")
async def paper_trade(opportunity_id: str):
    # Pre-flight refresh: simulations always use the newest available books.
    await refresh(app)
    item=next((x for x in runtime.opportunities if x.id==opportunity_id),None)
    if not item: raise HTTPException(404,"Opportunity not found; refresh and try again")
    trades=db.paper_trades(); available=settings.paper_balance-sum(x["capital_deployed"] for x in trades)
    trade=simulate(item,available); db.save_paper_trade(trade); return trade

@app.get("/api/paper/performance")
async def performance():
    trades=db.paper_trades(); filled=[x for x in trades if x["status"]=="SIMULATED_FILLED"]
    return {"trades":trades,"total_simulations":len(trades),"capital_deployed":sum(x["capital_deployed"] for x in filled),
            "theoretical_profit":sum(x["theoretical_profit"] for x in filled),
            "average_roi":sum(x["roi"] for x in filled)/len(filled) if filled else 0,
            "failed_hedge_simulations":sum(x["status"].startswith("FAILED") for x in trades),
            "stale_price_incidents":sum(x["status"]=="FAILED_STALE" for x in trades),
            "match_quality_incidents":sum(x["status"]=="FAILED_MATCH" for x in trades)}
