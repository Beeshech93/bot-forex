# Backend — Smart Signals FX

FastAPI service for a read-only Forex and XAU/USD signal platform. The backend
must never send, modify, or close MetaTrader 5 orders.

## Phase 1: API foundation

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

## Local setup

Requires Python 3.11 or newer.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

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

Every response includes an `X-Request-ID`. A safe incoming request ID is
preserved; otherwise one is generated. Logs avoid query strings and request
bodies.

## Tests

```powershell
python -m pytest
```

The tests cover health availability, request ID handling, authentication, and
fail-closed behavior when API authentication is not configured.
