# API Reference

All `/api/v1/*` routes require `Authorization: Bearer <API_TOKEN>`.
`GET /health` is public and returns only service liveness. Responses include
`X-Request-ID`. All timestamps are UTC.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Public service liveness |
| GET | `/api/v1/terminal` | MT5 availability, without account identifiers |
| GET | `/api/v1/symbols` | Symbols advertised by the connected terminal |
| GET | `/api/v1/candles?symbol=EURUSD&timeframe=M5&limit=100` | Up to 1,000 closed bars |
| GET | `/api/v1/indicators?symbol=EURUSD&timeframe=M5` | EMA 20/50, RSI 14, ATR 14 and chart series |
| GET | `/api/v1/signals?symbol=EURUSD&timeframe=M5` | Current analysis and theoretical levels |
| GET | `/api/v1/signals/history?limit=50` | Persisted signal history |
| POST | `/api/v1/backtest` | Run a historical simulation; never sends broker orders |
| GET | `/api/v1/backtest/{id}` | Read a persisted result |
| GET | `/api/v1/metrics` | Aggregate persisted backtest metrics |
| GET | `/api/v1/config` | Read active strategy parameters |
| PUT | `/api/v1/config` | Validate and persist strategy parameters |

Supported timeframes are M5 and M15. Candle request limits and symbols are
validated. MT5 shift zero (the forming candle) is excluded. Backtest requests
accept timezone-aware start/end times, a maximum of 20,000 bars, spread and
slippage assumptions, and optional strategy parameters.

There are deliberately no trading endpoints.
