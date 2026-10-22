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

Import the repository, select `frontend` as the Root Directory, and configure
`BACKEND_API_URL`, `BACKEND_API_TOKEN`, `DASHBOARD_PASSWORD`, and `SESSION_SECRET` as server-side environment variables
for the required deployment environments. Do not prefix them with
`NEXT_PUBLIC_`. Deploy the backend separately to a Windows VPS; a Vercel
function cannot host the MetaTrader5 Python terminal integration.

## Pages

- `/` — service and terminal status, latest available analysis.
- `/market` — M5/M15 candles, EMA overlays, RSI, and ATR.
- `/signals` — BUY, SELL, or NO_SIGNAL with theoretical reference levels.
- `/backtesting` — historical simulation and CSV export.
- `/settings` — editable, backend-validated strategy parameters and security state.

