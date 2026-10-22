# Frontend — Smart Signals FX

Next.js App Router, TypeScript, React, Tailwind CSS 4, and Lightweight Charts.

## Local development

```bash
npm install
cp .env.example .env.local
npm run dev
```

Set `BACKEND_API_URL` to the backend origin and `BACKEND_API_TOKEN` to the same
random token configured by the backend. Both are server-only variables. The
browser calls `/api/proxy/*`; that route forwards only the read-only API paths
needed by the UI and never forwards order commands. Also set `DASHBOARD_PASSWORD`
and a random `SESSION_SECRET` of at least 32 characters. Pages require that
password and receive a signed, HTTP-only, eight-hour session cookie. These
variables are server-only too.

## Vercel deployment

The repository-root `vercel.json` declares a Vercel Services project with a
public Next.js frontend and a private FastAPI backend. The frontend calls the
backend through the server-side `BACKEND_URL` service binding. Vercel injects
that variable at function runtime; do not configure it manually. Set
`BACKEND_API_TOKEN`, `DASHBOARD_PASSWORD`, and `SESSION_SECRET` as server-side
environment variables for the appropriate services/environments. Keep
`API_TOKEN` on the backend equal to `BACKEND_API_TOKEN` on the frontend. Never
prefix secrets with `NEXT_PUBLIC_`.

`BACKEND_API_URL` is only a fallback for local development or standalone
frontend deployments. It is not needed for the Vercel binding.

**MT5 limitation:** Vercel's FastAPI service runs on Linux, while this project's
MetaTrader 5 adapter is Windows-only. The backend can deploy there, but it
will report MT5 as unsupported and cannot supply live terminal data. Keep the
MT5-connected backend on the Windows VPS for live data; that requires a
standalone frontend using `BACKEND_API_URL` rather than this internal Vercel
service binding.

## Pages

- `/` — service and terminal status, latest available analysis.
- `/market` — M5/M15 candles, EMA overlays, RSI, and ATR.
- `/signals` — BUY, SELL, or NO_SIGNAL with theoretical reference levels.
- `/backtesting` — historical simulation and CSV export.
- `/settings` — editable, backend-validated strategy parameters and security state.

