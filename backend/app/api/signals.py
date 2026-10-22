"""Read-only signal generation endpoint."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.security import require_api_token
from app.services.market_service import InsufficientMarketDataError, market_service
from app.services.mt5_service import MT5UnavailableError
from app.strategies.ema_rsi_atr import StrategyConfig, generate_signal

router = APIRouter(prefix="/api/v1", tags=["signals"], dependencies=[Depends(require_api_token)])


@router.get("/signals", summary="Generate a read-only signal from closed candles")
async def signal(
    symbol: str = Query(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
    timeframe: Literal["M5", "M15"] = "M5",
) -> dict[str, object]:
    try:
        candles = market_service.get_closed_candles(symbol, timeframe, 200)
    except (MT5UnavailableError, InsufficientMarketDataError) as exc:
        return {
            "direction": "NO_SIGNAL", "symbol": symbol, "timeframe": timeframe,
            "reference_price": None, "stop_loss": None, "take_profit": None,
            "generated_at": None, "last_closed_candle_time": None,
            "data_valid": False, "reasons": [str(exc)], "indicators": {},
        }
    result = generate_signal(symbol, timeframe, candles, StrategyConfig())
    return result.model_dump(mode="json")
