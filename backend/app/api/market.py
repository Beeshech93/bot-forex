"""Read-only market data and indicator endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.security import require_api_token
from app.services.market_service import InsufficientMarketDataError, calculate_indicators, market_service
from app.services.mt5_service import MT5UnavailableError

router = APIRouter(prefix="/api/v1", tags=["market"], dependencies=[Depends(require_api_token)])


@router.get("/candles", summary="Get closed market candles")
async def candles(
    symbol: str = Query(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
    timeframe: Literal["M5", "M15"] = "M5",
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, object]:
    try:
        rows = market_service.get_closed_candles(symbol, timeframe, limit)
    except MT5UnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "mt5_unavailable", "message": str(exc)}) from exc
    except InsufficientMarketDataError as exc:
        raise HTTPException(status_code=422, detail={"code": "market_data_unavailable", "message": str(exc)}) from exc
    return {"symbol": symbol, "timeframe": timeframe, "timezone": "UTC", "count": len(rows), "items": rows}


@router.get("/indicators", summary="Calculate EMA, RSI, and ATR from closed candles")
async def indicators(
    symbol: str = Query(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
    timeframe: Literal["M5", "M15"] = "M5",
    limit: int = Query(default=200, ge=50, le=1000),
) -> dict[str, object]:
    try:
        rows = market_service.get_closed_candles(symbol, timeframe, limit)
        result = calculate_indicators(rows)
    except MT5UnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "mt5_unavailable", "message": str(exc)}) from exc
    except InsufficientMarketDataError as exc:
        raise HTTPException(status_code=422, detail={"code": "market_data_unavailable", "message": str(exc)}) from exc
    latest = result.iloc[-1]
    values = {name: (float(latest[name]) if latest[name] == latest[name] else None) for name in ("ema_fast", "ema_slow", "rsi", "atr")}
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "timezone": "UTC",
        "last_closed_candle_time": latest["time"],
        "periods": {"ema_fast": 20, "ema_slow": 50, "rsi": 14, "atr": 14},
        "values": values,
        "series": [
            {"time": row["time"], "ema_fast": (float(row["ema_fast"]) if row["ema_fast"] == row["ema_fast"] else None),
             "ema_slow": (float(row["ema_slow"]) if row["ema_slow"] == row["ema_slow"] else None)}
            for _, row in result.iterrows()
        ],
    }
