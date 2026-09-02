# ARBITRAGE TERMINAL

A local, paper-first prediction-market arbitrage scanner for Polymarket and Kalshi. It compares contract resolution rules, walks executable order-book depth, includes explicit fees, applies conservative risk gates, and records simulated fills in SQLite.

It does **not** promise guaranteed profit. Displayed prices, contract equivalence, fees, latency, partial fills, platform rules, and settlement behavior can invalidate apparent arbitrage. Live trading is deliberately unavailable in this build.

## Start in five commands

Python 3.11 or newer is required.

```bash
cd path/to/ARBITRE
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Stop with `Ctrl+C` in the terminal. On later starts, run `source .venv/bin/activate` and the `uvicorn` command again.

## Modes and configuration

The safe default `DEMO_MODE=true` uses synthetic, visibly labeled books so the entire workflow works without credentials. Set `DEMO_MODE=false` in `.env` to query current public REST data. Public Polymarket and Kalshi market data do not require credentials. Kalshi WebSockets do require API authentication, so this version uses REST polling for its common read-only ingestion path.

Secrets belong only in `.env`, which Git ignores. Never paste a private key into the browser. `LIVE_TRADING_ENABLED` has no effect: the application contains a hard safety boundary and no functioning live router.

Important controls in `.env`:

- `MIN_NET_ROI` and `MIN_EXPECTED_PROFIT`: minimum modeled economics.
- `MAX_CAPITAL_PER_OPPORTUNITY` and `MAX_TOTAL_EXPOSURE`: exposure ceilings.
- `MAX_BOOK_AGE_SECONDS`: rejects stale snapshots.
- `MIN_LIQUIDITY`: minimum common contract depth.
- `MIN_MATCH_CONFIDENCE`: defaults to `VERIFIED`.
- `PAPER_BALANCE`: starting virtual balance.

## Reading the dashboard

`VERIFIED` means the deterministic matcher found very strong textual/rule agreement without identified rule differences; it is not a promise of identical real-world settlement. `LIKELY` and `AMBIGUOUS` require human review. `STALE` means the order book exceeded the age limit. Capacity is the total modeled capital consumed at the maximum common depth under the configured capital ceiling. Net profit is minimum basket payout minus walked-book cost and modeled fees.

Click a row to inspect both legs, VWAP, number of levels consumed, fees, slippage, payout, resolution analysis, and rejected risk gates. **SIMULATE EXECUTION** records a paper fill; it never sends an exchange order. The Paper Performance tab shows cumulative theoretical results and incidents. The SQLite file is `arbitrage_terminal.db` by default.

## Tests

```bash
source .venv/bin/activate
pytest -q
```

Tests cover order-book walking, partial depth, VWAP, fee models, capital sizing, matching, threshold/cutoff mismatches, staleness, scanner economics, and failed paper fills.

## Data-source notes

The connectors target Polymarket Gamma/CLOB endpoints for discovery, books, and fees, and Kalshi Trade API v2 for public markets and order books. Kalshi returns YES and NO bids, so the connector derives executable asks using binary-complement prices. Exchange endpoints, schemas, fee schedules, market rules, and availability can change; verify them before relying on live data. If a fee cannot be verified, the risk engine blocks the opportunity rather than treating it as fee-free.

## Architecture and limitations

FastAPI serves the dashboard and API. Exchange connectors normalize market data, the matcher compares resolution rules, the depth calculator walks executable levels, and the risk engine gates opportunities before the paper executor records them in SQLite. The frontend is plain HTML, CSS, and JavaScript.

This is an educational, paper-first tool. It has no live order router, authentication flow, guaranteed execution, portfolio reconciliation, or legal/tax advice. Matching is heuristic and must be reviewed by a human. Network access and exchange API changes can make scans incomplete or stale.

## Public-release hygiene

Runtime databases, local environments, logs, editor settings, and `.env` files are ignored. Copy `.env.example` to `.env` and keep credentials outside version control. The example file contains no secrets.
