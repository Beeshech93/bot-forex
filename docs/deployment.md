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

The environment this project was built in is macOS, so a real MT5 connection on
the Windows VPS remains to be verified. The Windows terminal must already be
connected; this backend does not perform broker login.

## Frontend on Vercel

1. Import the GitHub repository and set `frontend` as the Root Directory.
2. Add `BACKEND_API_URL` (HTTPS origin), `BACKEND_API_TOKEN`,
   `DASHBOARD_PASSWORD`, and `SESSION_SECRET` to Vercel's server-side environment
   variables. Never use `NEXT_PUBLIC_` for any secret.
3. Build and deploy the frontend. Keep the MT5-dependent backend on Windows.
4. Verify service and terminal status, authenticated symbol/market calls, and
   expected disconnected behavior before relying on market data.

The backtest endpoint is synchronous and bounded to 20,000 candles. Set a
reverse-proxy request timeout appropriate for the VPS and consider a background
job queue for longer ranges. `create_all` initializes tables but does not
migrate schema changes; back up PostgreSQL and add versioned migrations before
future schema changes.
