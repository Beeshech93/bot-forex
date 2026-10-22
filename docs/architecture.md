# Architecture

```text
Browser → Next.js on Vercel → authenticated, allowlisted API proxy → FastAPI on Windows VPS → MetaTrader 5 terminal
                                                                  ↘ SQLite (local) / PostgreSQL (deployment)
```

The MT5 service exposes terminal status, symbols, and closed OHLC candles only.
The strategy and backtest modules are pure analysis code. There are no API
methods or service calls for creating, changing, or closing broker orders.

FastAPI protects `/api/v1/*` with a bearer token; `/health` exposes only service
liveness. The Next.js proxy holds the backend token server-side, requires a
signed HTTP-only dashboard session, and permits a fixed set of market and
analysis routes. CORS is restricted to configured frontend origins.

Backtests, signals, and strategy settings are persisted in SQLAlchemy JSON
tables. SQLite is the local default; configure PostgreSQL with `DATABASE_URL`.
Tables are currently created from ORM metadata at startup; versioned migrations
and per-user identity/preferences remain future work. Dashboard login is a
single shared password session, so production multi-user deployments need an
identity provider and per-user authorization.
