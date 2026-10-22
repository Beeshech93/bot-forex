# Backend — Smart Signals FX

FastAPI service for a read-only Forex and XAU/USD signal platform. The backend
must never send, modify, or close MetaTrader 5 orders.

## Phase 1: API foundation

Phase 1 provides application configuration, JSON logging, request IDs, a public
`GET /health` endpoint, bearer-token protection for non-health endpoints, CORS
configuration, and OpenAPI documentation in development. The terminal route is
an authenticated status placeholder until the read-only MT5 connector is added
in Phase 2.

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
- `GET /api/v1/terminal` — authenticated placeholder (`not_configured`) until Phase 2.

Every response includes an `X-Request-ID`. A safe incoming request ID is
preserved; otherwise one is generated. Logs avoid query strings and request
bodies.

## Tests

```powershell
python -m pytest
```

The tests cover health availability, request ID handling, authentication, and
fail-closed behavior when API authentication is not configured.
