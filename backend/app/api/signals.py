"""Read-only signal generation endpoint."""

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SignalRecord
from app.security import require_api_token
from app.services.market_service import InsufficientMarketDataError, market_service
from app.services.config_service import current_strategy_config
from app.services.mt5_service import MT5UnavailableError
from app.strategies.ema_rsi_atr import StrategyConfig, generate_signal

router = APIRouter(prefix="/api/v1", tags=["signals"], dependencies=[Depends(require_api_token)])


@router.get("/signals", summary="Generate a read-only signal from closed candles")
def signal(
    symbol: str = Query(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._-]+$"),
    timeframe: Literal["M5", "M15"] = "M5",
    db: Session = Depends(get_db),
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
    config = current_strategy_config(db)
    result = generate_signal(symbol, timeframe, candles, config)
    payload = result.model_dump(mode="json")
    candle_time = result.last_closed_candle_time.isoformat() if result.last_closed_candle_time else None
    if candle_time:
        existing = db.scalar(select(SignalRecord.id).where(
            SignalRecord.symbol == symbol,
            SignalRecord.timeframe == timeframe,
            SignalRecord.candle_time == candle_time,
        ))
        if existing is None:
            db.add(SignalRecord(id=str(uuid4()), symbol=symbol, timeframe=timeframe,
                                candle_time=candle_time, direction=result.direction, payload=payload))
            db.commit()
    return payload


@router.get("/signals/history", summary="Read persisted signal history")
def signal_history(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> dict[str, object]:
    records = db.scalars(select(SignalRecord).order_by(SignalRecord.created_at.desc()).limit(limit)).all()
    return {"count": len(records), "items": [record.payload for record in records]}
