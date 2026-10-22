# Deployment

## Backend on a Windows VPS

1. Install Python 3.11 or newer (64-bit) and MetaTrader 5 from the broker or
   MetaQuotes. Open the terminal and connect it to the broker manually.
2. Clone the repository and enter `backend/`.
3. Create and activate a virtual environment, then install
   `requirements.txt` and `requirements-dev.txt`.
4. Copy `.env.example` to `.env`; set a random `API_TOKEN` with at least 32
   characters and the exact allowed `CORS_ORIGINS`. Set `MT5_TERMINAL_PATH` if
   automatic terminal discovery is not suitable. Do not put secrets in Git.
   For deployment use PostgreSQL and set `DATABASE_URL` to a private
   `postgresql+psycopg://` connection string.
5. Run `python -m pytest`, then start with
   `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
6. Put an HTTPS reverse proxy in front of FastAPI, keep the service port private,
   configure a Windows service manager for restart-on-failure, and verify
   `/health`, authenticated `/api/v1/terminal`, and `/api/v1/symbols`.

After the service is running, open PowerShell in the repository root and run
the read-only demo acceptance check. Set the API URL and token in the current
PowerShell session (the token is never printed):

```powershell
$env:SMART_SIGNALS_API_URL = "https://signals.example.com"
$env:SMART_SIGNALS_API_TOKEN = "<backend API token>"
./scripts/verify-mt5-demo.ps1 -Symbol EURUSD -Timeframe M5
```

Use the broker's exact symbol name if it differs (for example, `EURUSD.a`).
The script checks API health, authenticated terminal connectivity, symbol
availability, at least 50 UTC closed candles, indicators, and a valid signal
response. A successful run confirms read-only demo data access; it does not
verify order execution because the application intentionally has no trading
operations.

The environment this project was built in is macOS, so a real MT5 connection on
the Windows VPS remains to be verified. The Windows terminal must already be
connected; this backend does not perform broker login.

## Multi-service Vercel project

The repository-root `vercel.json` declares `frontend` (Next.js) and `backend`
(FastAPI) services. All public paths route to the frontend so its `/api/auth/*`
and `/api/proxy/*` handlers continue to work. The backend remains internal;
the frontend's server-side proxy calls it through Vercel's `BACKEND_URL`
service binding. This avoids routing browser requests around the session and
API allowlist checks in the frontend.

Set `BACKEND_API_TOKEN` on the frontend and the matching `API_TOKEN` on the
backend. Also set `DASHBOARD_PASSWORD` and `SESSION_SECRET` for the frontend,
and configure a durable PostgreSQL `DATABASE_URL` for the backend. Do not set
`BACKEND_URL` manually; Vercel injects it from the binding. Keep all secrets
server-side and do not use `NEXT_PUBLIC_` names.

**Live MT5 data is not available when both services run on Vercel.** Vercel's
FastAPI service runs on Linux and this repository's MT5 adapter only supports
Windows. To use a connected MT5 terminal, deploy the backend on the Windows VPS
described above and deploy the frontend separately with `BACKEND_API_URL` set
to that backend's HTTPS origin. A Vercel service binding only targets another
service in the same Vercel project, not an external Windows VPS.

The backtest endpoint is synchronous and bounded to 20,000 candles. Set a
reverse-proxy request timeout appropriate for the VPS and consider a background
job queue for longer ranges. `create_all` initializes tables but does not
migrate schema changes; back up PostgreSQL and add versioned migrations before
future schema changes.
