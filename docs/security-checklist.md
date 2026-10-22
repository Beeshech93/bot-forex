# Security and production checklist

- [ ] Create separate random secrets for `API_TOKEN` and `SESSION_SECRET`; use
  at least 32 characters. Set a unique `DASHBOARD_PASSWORD`.
- [ ] Keep `.env`, database credentials, and secrets out of Git and out of any
  `NEXT_PUBLIC_*` variable.
- [ ] Serve Vercel and the backend only over HTTPS. Bind FastAPI to localhost
  behind a reverse proxy and firewall the service port.
- [ ] Set `CORS_ORIGINS` to known frontend origins. The Next.js proxy also
  checks a signed, HTTP-only, SameSite=Strict session before forwarding
  protected requests.
- [ ] Protect the VPS and terminal with a non-administrator Windows service
  account. Keep MetaTrader 5 logged in manually and do not store broker
  credentials in this project.
- [ ] Use a private PostgreSQL database with a restricted application role,
  encrypted transport, backups, and restore checks.
- [ ] Add edge or reverse-proxy rate limiting. The current API limiter is
  process-local and does not coordinate multiple workers.
- [ ] Add versioned database migrations and an identity provider before
  multi-user access. The current dashboard password is shared.
- [ ] Verify that no endpoint or code path places, changes, or closes orders.
- [ ] Run the unit suite and frontend production build. Test the terminal
  against a demo account on the target Windows VPS before enabling the dashboard.
- [ ] Display clear stale-data status and preserve the no-guaranteed-returns
  language. Historical results do not predict future performance.
