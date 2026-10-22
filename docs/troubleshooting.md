# Troubleshooting

## `GET /health` is unavailable

Confirm the FastAPI process is running, the reverse proxy points to its local
port, and the VPS firewall allows the proxy's HTTPS endpoint. `/health` does
not confirm MT5 connectivity.

## Terminal reports disconnected or unsupported

The connector is supported only on Windows and requires the MetaTrader 5
Python package, terminal installation, and an already connected broker
session. Verify the terminal path and run the service under the same Windows
account that owns the terminal session. This service never logs in for you.

## Symbols or candles are missing

Check authenticated `GET /api/v1/symbols` for the broker's exact symbol name.
Symbol names such as `XAUUSD.a` must be used as returned. Confirm history is
available for that symbol and M5/M15 in the terminal. The live, forming bar is
excluded. Insufficient or out-of-order bars do not produce a signal.

## API returns 401 or 503

401 indicates a missing or incorrect bearer token. 503 indicates the backend
token is not configured or the terminal/service dependency is unavailable.
Ensure Vercel `BACKEND_API_TOKEN` matches backend `API_TOKEN` exactly. Neither
value should appear in a browser bundle.

## Dashboard redirects to login

Set `DASHBOARD_PASSWORD` and a `SESSION_SECRET` of at least 32 characters in
the frontend server environment, then restart/redeploy. Sessions last eight
hours; log in again after expiry.

## Backtest returns 422 or 503

Use timezone-aware dates, start before end, M5 or M15, a valid broker symbol,
and a range containing sufficient history. The range is capped at 20,000 bars.
503 means historical rates could not be read from MT5.

Backtest P/L is quoted in one-unit position price units and models supplied
spread/slippage only. Commission, swaps, gaps, latency, and live execution are
not fully reproduced.
