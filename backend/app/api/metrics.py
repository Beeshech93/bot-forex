"""Read-only aggregated historical simulation metrics."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import BacktestRecord
from app.security import require_api_token

router = APIRouter(prefix="/api/v1", tags=["metrics"], dependencies=[Depends(require_api_token)])


@router.get("/metrics", summary="Aggregate persisted backtest metrics")
def metrics(db: Session = Depends(get_db)) -> dict[str, object]:
    records = db.scalars(select(BacktestRecord).order_by(BacktestRecord.created_at.desc())).all()
    trades = [trade for record in records for trade in record.payload.get("trades", [])]
    profits = [float(trade["pnl"]) for trade in trades if float(trade["pnl"]) > 0]
    losses = [-float(trade["pnl"]) for trade in trades if float(trade["pnl"]) < 0]
    pnl = sum(float(trade["pnl"]) for trade in trades)
    wins = len(profits)
    grouped: dict[str, dict[str, object]] = {}
    for record in records:
        key = f"{record.symbol}:{record.timeframe}"
        aggregate = grouped.setdefault(key, {"symbol": record.symbol, "timeframe": record.timeframe,
                                               "backtest_count": 0, "trade_count": 0, "net_pnl": 0.0})
        aggregate["backtest_count"] = int(aggregate["backtest_count"]) + 1
        aggregate["trade_count"] = int(aggregate["trade_count"]) + record.trade_count
        aggregate["net_pnl"] = float(aggregate["net_pnl"]) + float(record.payload.get("net_pnl", 0.0))
    return {
        "backtest_count": len(records), "trade_count": len(trades),
        "win_rate": wins / len(trades) if trades else 0.0, "net_pnl": pnl,
        "profit_factor": sum(profits) / sum(losses) if losses else None,
        "max_drawdown": max((float(row.payload.get("max_drawdown", 0.0)) for row in records), default=0.0),
        "expectancy": pnl / len(trades) if trades else 0.0,
        "by_symbol_timeframe": list(grouped.values()),
    }
