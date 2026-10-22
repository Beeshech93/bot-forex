# Smart Signals FX

Read-only signal-generation platform for Forex and XAU/USD. It does not execute
trades or modify broker orders.

## Current status

Phase 1 backend foundation is in `backend/`: FastAPI, validated settings,
bearer-token protection, structured JSON logs, request IDs, and public
`GET /health`. The authenticated terminal endpoint remains a Phase 2
placeholder. MetaTrader 5 integration and signal generation are not yet
implemented.

See [backend/README.md](backend/README.md) for local setup and endpoint details.
