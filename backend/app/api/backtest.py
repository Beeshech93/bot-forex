"""Authenticated historical simulation endpoints."""

from datetime import timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backtesting.engine import BacktestRequest, run_backtest
from app.database import get_db
from app.models import BacktestRecord
from app.security import require_api_token
from app.services.market_service import InsufficientMarketDataError
from app.services.mt5_service import MT5UnavailableError, mt5_service

router = APIRouter(prefix="/api/v1", tags=["backtesting"], dependencies=[Depends(require_api_token)])


@router.post("/backtest", summary="Run a historical simulation without trading")
def create_backtest(payload: BacktestRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        request = payload.validate_range()
        start = request.start_date.astimezone(timezone.utc)
        end = request.end_date.astimezone(timezone.utc)
        candles = mt5_service.candles_between(request.symbol, request.timeframe, start, end, 20_000)
        result = run_backtest(candles, request)
    except (ValueError, InsufficientMarketDataError) as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_backtest", "message": str(exc)}) from exc
    except MT5UnavailableError as exc:
        raise HTTPException(status_code=503, detail={"code": "mt5_unavailable", "message": str(exc)}) from exc
    result_id = str(uuid4())
    payload_json = result.model_dump(mode="json")
    db.add(BacktestRecord(id=result_id, symbol=result.symbol, timeframe=result.timeframe,
                          trade_count=result.trade_count, payload=payload_json))
    db.commit()
    return {"id": result_id, "status": "completed", "result": payload_json}


@router.get("/backtest/{result_id}", summary="Read a completed simulation result")
def get_backtest(result_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    record = db.get(BacktestRecord, result_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "backtest_not_found", "message": "Backtest result was not found"})
    return {"id": result_id, "status": "completed", "result": record.payload}
