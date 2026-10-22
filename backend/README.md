# Backend — Smart Signals FX

FastAPI service for a read-only Forex and XAU/USD signal platform. The backend
must never send, modify, or close MetaTrader 5 orders.

## Implemented API foundation and analysis

Phases 1 and 2 provide application configuration, JSON logging, request IDs, a
public `GET /health` endpoint, bearer-token protection for non-health endpoints,
CORS configuration, development OpenAPI docs, a read-only MT5 adapter, and
authenticated terminal and symbol endpoints. The MT5 adapter does not log in
to accounts or expose any order execution methods. On non-Windows systems its
status reports that the terminal platform is unsupported.

Phase 3 adds bounded candle retrieval (M5/M15 only), excludes MT5 shift-zero
forming bars, normalizes times to UTC, validates chronological data, and
calculates EMA 20/50, RSI 14, and ATR 14.

Phase 4 adds `GET /api/v1/signals`, which returns BUY, SELL, or NO_SIGNAL using
trend, closed-candle EMA crossing, RSI, ATR, and optional spread checks. SL and
TP are analytic reference levels derived from ATR. No order methods are
implemented or invoked.

The backtest engine uses only historical data through the signal candle, enters
on the following bar, accounts for configurable spread/slippage, and assumes
stop loss first when both SL and TP are touched in one OHLC candle. Backtests,
signal history, and strategy configuration are stored in SQLite locally or
PostgreSQL when `DATABASE_URL` is configured. The Next.js UI is in `../frontend`.

## Local setup

Requires Python 3.11 or newer.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

On macOS/Linux use `python3 -m venv .venv`, activate `.venv`, and use `cp` for
the environment file. `MetaTrader5` is installed only on Windows; unit tests
mock its interface and do not require a real account.

Replace `API_TOKEN` in `.env` with a random secret of at least 32 characters.
Never commit `.env`. `GET /health` remains public; `/api/v1/*` routes require
`Authorization: Bearer <API_TOKEN>`.

Start the development server from this directory:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

OpenAPI docs are available at `/docs` outside production. In production, set
`ENVIRONMENT=production` to disable the docs routes. Set `CORS_ORIGINS` to a
JSON array of explicitly allowed frontend origins.

## Endpoints in this phase

- `GET /health` — public service liveness without host, account, or credential data.
- `GET /api/v1/terminal` — authenticated connection status without account identifiers.
- `GET /api/v1/symbols` — authenticated symbols from the connected terminal.
- `GET /api/v1/candles?symbol=EURUSD&timeframe=M5&limit=100` — up to 1,000 closed bars.
- `GET /api/v1/indicators?symbol=EURUSD&timeframe=M15` — latest EMA/RSI/ATR values.
- `GET /api/v1/signals?symbol=EURUSD&timeframe=M5` — read-only current analysis and reference levels.
- `GET /api/v1/signals/history` — persisted signal history.
- `GET /api/v1/config` and `PUT /api/v1/config` — read and update validated strategy parameters.
- `POST /api/v1/backtest` and `GET /api/v1/backtest/{id}` — run and retrieve persisted simulations.
- `GET /api/v1/metrics` — aggregate stored backtest metrics.

Every response includes an `X-Request-ID`. A safe incoming request ID is
preserved; otherwise one is generated. Logs avoid query strings and request
bodies.

## Tests

```powershell
python -m pytest
```

The tests cover health, authentication, mocked MT5 access, closed-candle
retrieval, indicators, signals, and backtest look-ahead and collision behavior.
