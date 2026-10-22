# Smart Signals FX

Read-only signal-generation platform for Forex and XAU/USD. It does not execute
trades or modify broker orders.

## Current status

Implemented so far: FastAPI foundation and token auth; read-only MT5 status and
symbol listing; closed M5/M15 candles; EMA/RSI/ATR indicators; BUY/SELL/
NO_SIGNAL analysis; causal OHLC backtesting; and a responsive Next.js dashboard
with server-side API proxying and CSV export.

Backtest results, signal history, and strategy settings use SQLAlchemy with
SQLite locally or PostgreSQL via `DATABASE_URL`. The dashboard uses a server-side
password session and keeps backend credentials off the browser. Database
migrations, per-user identity/preferences, edge-level rate limiting, and live
Windows MT5 validation remain before production acceptance. The backtest
endpoint is synchronous and needs deployment-specific duration limits.

See [backend/README.md](backend/README.md) for API and Windows setup and
[frontend/README.md](frontend/README.md) for local development and Vercel setup.
